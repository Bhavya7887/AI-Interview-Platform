
import time

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render

from .ai_engine import generate_question_data, evaluate_answer
from .forms import InterviewSetupForm
from .models import Interview, InterviewQuestion, InterviewResponse


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                "Your account is ready. Let's start practising!",
            )
            return redirect("dashboard")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    interviews = Interview.objects.filter(
        owner=request.user
    ).order_by("-created_at")

    completed = interviews.filter(completed=True)

    response_stats = InterviewResponse.objects.filter(
        interview__owner=request.user
    ).aggregate(
        average=Avg("score"),
        count=Count("id"),
    )

    return render(request, "interviews/dashboard.html", {
        "interviews": interviews[:10],
        "total_interviews": interviews.count(),
        "completed_interviews": completed.count(),
        "average_score": round(response_stats["average"] or 0, 1),
        "total_answers": response_stats["count"],
    })


@login_required
def home(request):
    if request.method == "POST":
        # request.FILES is required for resume uploads.
        form = InterviewSetupForm(request.POST, request.FILES)

        if form.is_valid():
            interview = form.save(commit=False)
            interview.owner = request.user

            if interview.level == "Fresher":
                interview.difficulty = "Easy"
            elif interview.level in ("Junior", "Mid-Level"):
                interview.difficulty = "Medium"
            else:
                interview.difficulty = "Hard"

            interview.save()

            return redirect(
                "interview_detail",
                public_id=interview.public_id,
            )
    else:
        form = InterviewSetupForm(
            initial={
                "number_of_questions": 5,
                "seconds_per_question": 90,
            }
        )

    return render(request, "interviews/home.html", {"form": form})


def _ensure_current_question(interview):
    """Return the current question or create it using the structured AI engine."""
    if interview.completed:
        return None

    order = interview.current_question + 1

    question = interview.questions.filter(order=order).first()
    if question:
        return question

    if order > interview.number_of_questions:
        interview.completed = True
        interview.save(update_fields=["completed"])
        return None

    previous = list(
        interview.questions.values_list("text", flat=True)
    )

    data = generate_question_data(interview, order, previous)

    return InterviewQuestion.objects.create(
        interview=interview,
        order=order,
        text=data["text"],
        question_type=data["question_type"],
        options=data.get("options", []),
        correct_answer=data.get("correct_answer", ""),
        skill=data.get("skill", "General"),
        explanation=data.get("explanation", ""),
        hint=data.get("hint", ""),
        difficulty=data.get("difficulty", interview.difficulty),
    )


@login_required
def interview_detail(request, public_id):
    interview = get_object_or_404(
        Interview,
        public_id=public_id,
        owner=request.user,
    )

    question = _ensure_current_question(interview)

    if question is None:
        return redirect("report", public_id=interview.public_id)

    try:
        response = question.response
    except InterviewResponse.DoesNotExist:
        response = None

    return render(request, "interviews/interview.html", {
        "interview": interview,
        "question": question,
        "response": response,
        "progress_percent": int(
            interview.current_question / interview.number_of_questions * 100
        ),
    })


@login_required
@transaction.atomic
def submit_answer(request, public_id):
    interview = get_object_or_404(
        Interview,
        public_id=public_id,
        owner=request.user,
    )

    if request.method != "POST":
        return redirect("interview_detail", public_id=public_id)

    if interview.completed:
        return redirect("report", public_id=public_id)

    question = _ensure_current_question(interview)

    if question is None:
        return redirect("report", public_id=public_id)

    # Prevent duplicate submissions for the same question.
    if InterviewResponse.objects.filter(question=question).exists():
        interview.current_question = max(
            interview.current_question,
            question.order,
        )
        interview.save(update_fields=["current_question"])

        return redirect("interview_detail", public_id=public_id)

    answer = request.POST.get("answer", "").strip()[:10000]

    try:
        elapsed = max(
            0,
            int(request.POST.get("elapsed_seconds", "0")),
        )
    except (TypeError, ValueError):
        elapsed = 0

    elapsed = min(elapsed, 3600)

    result = evaluate_answer(
        interview,
        question,
        answer,
        elapsed,
    )

    overtime = elapsed > interview.seconds_per_question
    score = max(0, min(10, int(result.get("score", 0))))

    if overtime and answer:
        score = max(0, score - 1)

    feedback = result.get("feedback", "")
    if overtime and answer:
        feedback += " (1 point deducted for exceeding the time limit.)"

    InterviewResponse.objects.create(
        interview=interview,
        question=question,
        answer=answer,
        score=score,
        topic=result.get("topic", question.skill or "General"),
        key_points=result.get("key_points", ""),
        ideal_answer=result.get("ideal_answer", ""),
        improvement_areas=result.get("improvement_areas", ""),
        feedback=feedback,
        elapsed_seconds=elapsed,
        overtime=overtime,
    )

    interview.current_question = question.order

    if interview.current_question >= interview.number_of_questions:
        interview.completed = True

    interview.save(update_fields=["current_question", "completed"])

    if interview.completed:
        return redirect("report", public_id=public_id)

    return redirect("interview_detail", public_id=public_id)


@login_required
def report(request, public_id):
    interview = get_object_or_404(
        Interview,
        public_id=public_id,
        owner=request.user,
    )

    responses = list(
        interview.responses.select_related("question").all()
    )

    avg_time = (
        round(
            sum(response.elapsed_seconds for response in responses)
            / len(responses),
            1,
        )
        if responses else 0
    )

    overtime_count = sum(
        1 for response in responses if response.overtime
    )

    strong_topics = list(dict.fromkeys(
        response.topic
        for response in responses
        if response.score >= 8
    ))

    weak_topics = list(dict.fromkeys(
        response.topic
        for response in responses
        if response.score < 6
    ))

    score_progress = [
        {
            "label": f"Q{response.question.order}",
            "score": response.score,
        }
        for response in responses
    ]

    return render(request, "interviews/report.html", {
        "interview": interview,
        "responses": responses,
        "avg_time": avg_time,
        "overtime_count": overtime_count,
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
        "score_progress": score_progress,
    })
