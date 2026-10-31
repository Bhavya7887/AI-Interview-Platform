import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class Interview(models.Model):
    LEVELS = [
        ("Fresher", "Fresher"),
        ("Junior", "Junior"),
        ("Mid-Level", "Mid-Level"),
        ("Senior", "Senior"),
        ("Lead", "Lead"),
    ]

    DIFFICULTIES = [
        ("Easy", "Easy"),
        ("Medium", "Medium"),
        ("Hard", "Hard"),
    ]

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interviews",
    )

    role = models.CharField(max_length=120)
    level = models.CharField(max_length=20, choices=LEVELS)
    job_description = models.TextField(blank=True)

    resume_file = models.FileField(
        upload_to="resumes/",
        blank=True,
        null=True,
    )

    number_of_questions = models.PositiveSmallIntegerField(default=5)
    seconds_per_question = models.PositiveSmallIntegerField(default=90)

    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTIES,
        default="Easy",
    )

    current_question = models.PositiveSmallIntegerField(default=0)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role} — {self.created_at:%Y-%m-%d}"

    @property
    def answered_count(self):
        return self.responses.count()

    @property
    def average_score(self):
        scores = list(self.responses.values_list("score", flat=True))
        return round(sum(scores) / len(scores), 1) if scores else 0

    def get_absolute_url(self):
        return reverse(
            "interview_detail",
            kwargs={"public_id": self.public_id},
        )


class InterviewQuestion(models.Model):
    TYPES = [
        ("mcq", "Multiple Choice"),
        ("true_false", "True / False"),
        ("short_answer", "Short Answer"),
        ("coding", "Coding Challenge"),
        ("debugging", "Debugging"),
        ("scenario", "Scenario Based"),
        ("follow_up", "Follow-up"),
        ("technical", "Technical"),
        ("behavioral", "Behavioral"),
        ("situational", "Situational"),
        ("problem-solving", "Problem-solving"),
    ]

    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    order = models.PositiveSmallIntegerField()
    text = models.TextField()

    question_type = models.CharField(
        max_length=30,
        choices=TYPES,
        default="technical",
    )

    # Example: ["List", "Tuple", "Dictionary", "Set"]
    options = models.JSONField(default=list, blank=True)

    # Store the expected answer for evaluation.
    # Do not display this field to the candidate before submission.
    correct_answer = models.TextField(blank=True)

    # Skill assessed by this question, e.g. Python, Django, SQL.
    skill = models.CharField(max_length=100, default="General")

    explanation = models.TextField(blank=True)
    hint = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=10,
        choices=Interview.DIFFICULTIES,
        default="Easy",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["interview", "order"],
                name="unique_question_order_per_interview",
            )
        ]

    def __str__(self):
        return f"Q{self.order}: {self.text[:70]}"


class InterviewResponse(models.Model):
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name="responses",
    )

    question = models.OneToOneField(
        InterviewQuestion,
        on_delete=models.CASCADE,
        related_name="response",
    )

    answer = models.TextField(blank=True)
    score = models.PositiveSmallIntegerField(default=0)

    topic = models.CharField(max_length=120, default="General")
    key_points = models.TextField(blank=True)
    ideal_answer = models.TextField(blank=True, default="")
    improvement_areas = models.TextField(blank=True, default="")
    feedback = models.TextField(blank=True)

    elapsed_seconds = models.PositiveIntegerField(default=0)
    overtime = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        ordering = ["question__order"]

    def __str__(self):
        return f"{self.interview.role}: {self.score}/10"


class LearningRoadmap(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learning_roadmaps",
    )

    interview = models.ForeignKey(
        Interview,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learning_roadmaps",
    )

    title = models.CharField(max_length=200)
    target_role = models.CharField(max_length=120, default="Python Developer")
    duration_days = models.PositiveSmallIntegerField(default=7)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def total_tasks(self):
        return self.tasks.count()

    @property
    def completed_tasks(self):
        return self.tasks.filter(status="completed").count()

    @property
    def progress_percentage(self):
        total = self.total_tasks
        if not total:
            return 0
        return round(self.completed_tasks / total * 100)


class RoadmapTask(models.Model):
    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    roadmap = models.ForeignKey(
        LearningRoadmap,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    day_number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200)
    skill = models.CharField(max_length=100)
    description = models.TextField()
    exercise = models.TextField(blank=True)
    completion_criteria = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_started",
    )

    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["day_number", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["roadmap", "day_number", "title"],
                name="unique_roadmap_task_title_per_day",
            )
        ]

    def __str__(self):
        return f"Day {self.day_number}: {self.title}"