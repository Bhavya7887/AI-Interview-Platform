import json
import logging
from difflib import SequenceMatcher
import os
import random
import re

logger = logging.getLogger(__name__)

QUESTION_TYPES = [
    "mcq",
    "true_false",
    "short_answer",
    "coding",
    "debugging",
    "scenario",
]

# Fallback questions are used when Groq is unavailable or returns invalid data.
# Every fallback includes the fields needed by the upgraded interview engine.
FALLBACK_QUESTIONS = {
    "mcq": [
        {"text": "Which Python data type stores unique elements?", "options": ["List", "Tuple", "Set", "Dictionary"], "correct_answer": "Set", "skill": "Python", "explanation": "A set stores unique elements.", "hint": "Think of the collection that removes duplicates."},
        {"text": "Which HTTP method is normally used to retrieve a resource?", "options": ["POST", "GET", "PATCH", "DELETE"], "correct_answer": "GET", "skill": "REST APIs", "explanation": "GET is used to retrieve a resource.", "hint": "Choose the read operation."},
        {"text": "What is the average time complexity of dictionary lookup in Python?", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct_answer": "O(1)", "skill": "Python Data Structures", "explanation": "Hash-table lookups are average O(1).", "hint": "Think about hash tables."},
        {"text": "Which Django component maps Python objects to database tables?", "options": ["Template", "Model", "Middleware", "URL pattern"], "correct_answer": "Model", "skill": "Django", "explanation": "Django models define data structure and ORM behavior.", "hint": "It is the M in MTV."},
        {"text": "Which SQL clause filters rows before grouping?", "options": ["ORDER BY", "HAVING", "WHERE", "LIMIT"], "correct_answer": "WHERE", "skill": "SQL", "explanation": "WHERE filters rows before aggregation.", "hint": "It appears before GROUP BY."},
        {"text": "Which status code commonly indicates a successful resource creation?", "options": ["200", "201", "400", "500"], "correct_answer": "201", "skill": "HTTP", "explanation": "201 Created indicates successful resource creation.", "hint": "It is the Created response."},
    ],
    "true_false": [
        {"text": "In Python, dictionaries store data as key-value pairs.", "options": ["True", "False"], "correct_answer": "True", "skill": "Python", "explanation": "Dictionaries map keys to values.", "hint": "Consider how a key retrieves its associated value."},
        {"text": "A Django model is commonly used to define database structure.", "options": ["True", "False"], "correct_answer": "True", "skill": "Django", "explanation": "Models describe fields and relationships.", "hint": "Think about the Django ORM."},
        {"text": "A Python tuple can always be modified in place after creation.", "options": ["True", "False"], "correct_answer": "False", "skill": "Python", "explanation": "Tuples are immutable, though they may contain mutable objects.", "hint": "Compare tuples with lists."},
        {"text": "HTTP is a stateless application-layer protocol.", "options": ["True", "False"], "correct_answer": "True", "skill": "Networking", "explanation": "Each request is independent unless state is added separately.", "hint": "Consider whether HTTP remembers prior requests by itself."},
        {"text": "Django migrations help propagate model changes into the database schema.", "options": ["True", "False"], "correct_answer": "True", "skill": "Django", "explanation": "Migrations version and apply schema changes.", "hint": "Think about makemigrations and migrate."},
        {"text": "A SQL LEFT JOIN returns only rows that have matches in both tables.", "options": ["True", "False"], "correct_answer": "False", "skill": "SQL", "explanation": "LEFT JOIN preserves all rows from the left table.", "hint": "What happens when the right-side match is missing?"},
    ],
    "short_answer": [
        {"text": "Explain the difference between a Python list and a tuple.", "options": [], "correct_answer": "Lists are mutable, while tuples are immutable. Both are ordered collections.", "skill": "Python", "explanation": "Mutability is the key distinction.", "hint": "Explain whether elements can be changed."},
        {"text": "What is the purpose of a virtual environment in a Python project?", "options": [], "correct_answer": "It isolates project dependencies and Python packages from other projects.", "skill": "Python Tooling", "explanation": "Isolation helps avoid dependency conflicts.", "hint": "Think about two projects needing different package versions."},
        {"text": "Explain how Django's URL dispatcher connects a URL to a view.", "options": [], "correct_answer": "URL patterns match the request path and route it to a view function or class.", "skill": "Django", "explanation": "URLconf maps paths to views.", "hint": "Mention urlpatterns and the matched view."},
        {"text": "What is the difference between authentication and authorization in an API?", "options": [], "correct_answer": "Authentication verifies identity; authorization determines what that identity may access.", "skill": "API Security", "explanation": "They solve different security questions.", "hint": "Who are you versus what may you do?"},
        {"text": "Why should database queries be parameterized?", "options": [], "correct_answer": "Parameterized queries separate data from SQL syntax and help prevent SQL injection.", "skill": "Database Security", "explanation": "Inputs are treated as values, not executable SQL.", "hint": "Think about untrusted user input."},
        {"text": "Describe the purpose of HTTP status codes in a REST API.", "options": [], "correct_answer": "They communicate the outcome of a request, such as success, client error, or server error.", "skill": "REST APIs", "explanation": "Clients use status codes to interpret responses.", "hint": "Give one success and one error example."},
    ],
    "coding": [
        {"text": "Write a Python function that returns the largest number in a non-empty list without using max().", "options": [], "correct_answer": "Initialize from the first element, scan the list, update the largest value, and return it.", "skill": "Python", "explanation": "One traversal takes O(n) time.", "hint": "Track the largest value seen so far."},
        {"text": "Write a Python function that counts how many vowels appear in a string.", "options": [], "correct_answer": "Iterate through the characters and count those in a set of vowels, handling case consistently.", "skill": "Python Strings", "explanation": "A single pass takes O(n) time.", "hint": "Normalize case and check membership."},
        {"text": "Write a function that removes duplicates from a list while preserving the original order.", "options": [], "correct_answer": "Track seen values in a set and append each value only on its first occurrence.", "skill": "Python Data Structures", "explanation": "A set tracks membership efficiently.", "hint": "Use a seen set and a result list."},
        {"text": "Write a Python function that determines whether a string is a palindrome, ignoring spaces and letter case.", "options": [], "correct_answer": "Normalize case and spaces, then compare the string with its reverse or use two pointers.", "skill": "Algorithms", "explanation": "Normalization is needed before comparison.", "hint": "Compare matching characters from both ends."},
        {"text": "Write a function that returns the frequency of each word in a sentence.", "options": [], "correct_answer": "Split or tokenize the sentence and count each normalized word using a dictionary or Counter.", "skill": "Python Dictionaries", "explanation": "A hash map stores each word's count.", "hint": "Use a dictionary keyed by each word."},
        {"text": "Write a function that merges two sorted lists into one sorted list.", "options": [], "correct_answer": "Use two pointers to repeatedly take the smaller current item, then append remaining items.", "skill": "Algorithms", "explanation": "The merge step is linear in the combined length.", "hint": "Compare the front item of each list."},
    ],
    "debugging": [
        {"text": "Find and fix the bug: for i in range(len(items) + 1): print(items[i])", "options": [], "correct_answer": "The loop goes one index past the end; use range(len(items)) or iterate over items directly.", "skill": "Python Debugging", "explanation": "Valid indexes end at len(items) - 1.", "hint": "Check the final index generated by range()."},
        {"text": "Why does this code fail for integer division: result = 5 / 2; print(result == 2)? Fix it if whole-number division is intended.", "options": [], "correct_answer": "In Python 3, / returns a float; use // for floor division when an integer quotient is intended.", "skill": "Python Operators", "explanation": "The result of 5 / 2 is 2.5.", "hint": "Compare / with //."},
        {"text": "Find the issue: if user_name = 'Bhavya': print('hello')", "options": [], "correct_answer": "The condition uses assignment syntax; use == for comparison and add the required colon/newline structure.", "skill": "Python Syntax", "explanation": "Equality comparison uses ==.", "hint": "Check the operator used in the if condition."},
        {"text": "A Django view returns a 'no such table' OperationalError after a model was added. What should you check and run?", "options": [], "correct_answer": "Confirm the app is installed, create migrations with makemigrations, and apply them with migrate.", "skill": "Django Debugging", "explanation": "The database schema may not include the new model/table.", "hint": "Think about Django's migration workflow."},
        {"text": "Find the likely bug: values = [1, 2, 3]; print(values[3])", "options": [], "correct_answer": "Index 3 is out of range for a three-element list; use a valid index or iterate safely.", "skill": "Python Debugging", "explanation": "The valid indexes are 0, 1, and 2.", "hint": "Remember indexing starts at zero."},
        {"text": "A function unexpectedly changes the caller's list after appending an item. Explain why and suggest a fix if mutation is unwanted.", "options": [], "correct_answer": "Lists are mutable and the function may hold a reference to the same object; copy the list before modifying it.", "skill": "Python Mutability", "explanation": "Assignment does not copy a list.", "hint": "Consider object references and list.copy()."},
    ],
    "scenario": [
        {"text": "A Django API becomes slow when returning hundreds of database records. How would you investigate and improve its performance?", "options": [], "correct_answer": "Measure the endpoint, inspect query counts, fix N+1 queries, paginate, and add indexes based on evidence.", "skill": "Django Performance", "explanation": "Measure the bottleneck before optimizing.", "hint": "Consider query count and response size."},
        {"text": "Users sometimes submit the same interview answer twice after double-clicking Submit. How would you prevent duplicate responses?", "options": [], "correct_answer": "Disable the button client-side and enforce server-side idempotency or a unique constraint/transaction.", "skill": "Backend Reliability", "explanation": "Client controls improve UX, but server-side protection is essential.", "hint": "Do not rely only on JavaScript."},
        {"text": "An API endpoint exposes one user's interview report to another logged-in user. What would you inspect and how would you fix it?", "options": [], "correct_answer": "Check object-level authorization and fetch records filtered by both identifier and request.user.", "skill": "Django Security", "explanation": "Authentication alone does not authorize access to every object.", "hint": "Look at the queryset in get_object_or_404."},
        {"text": "Your Django application works locally but fails on a fresh deployment because environment variables are missing. How would you make configuration reliable?", "options": [], "correct_answer": "Document required variables, validate settings at startup, configure deployment secrets, and provide safe defaults only where appropriate.", "skill": "Deployment", "explanation": "Environment-specific configuration should be explicit and secure.", "hint": "Consider .env files locally and secrets in production."},
        {"text": "A Groq request times out while generating an interview question. How should the application respond without losing the interview?", "options": [], "correct_answer": "Set timeouts/retries, log the failure, use a diverse fallback bank, and persist generated questions to avoid regeneration.", "skill": "AI Reliability", "explanation": "Graceful fallback preserves user progress.", "hint": "Think about graceful degradation."},
        {"text": "A resume upload endpoint accepts very large files and unexpected file types. What protections would you add?", "options": [], "correct_answer": "Validate file type and size, restrict extensions, store uploads safely, and avoid trusting client-supplied content types alone.", "skill": "File Upload Security", "explanation": "Uploads are untrusted input.", "hint": "Validate at the server, not only in the form."},
    ],
}


def _get_llm():
    """Create a Groq chat client, or return None if it is unavailable."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=api_key,
            temperature=0.3,
            max_retries=1,
        )
    except Exception:
        logger.exception("Could not initialize Groq client")
        return None


def _resume_text(interview):
    """
    Read resume text only if the project exposes it.

    The currently shared Interview model has resume_file but no resume_text
    field, so this avoids an AttributeError. Actual PDF/DOCX extraction can
    be connected here when its implementation is available.
    """
    value = getattr(interview, "resume_text", "")
    return value.strip() if isinstance(value, str) else ""


def _content_to_text(content):
    """Normalize common LangChain response content formats to text."""
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        return "\n".join(parts).strip()

    return str(content).strip() if content is not None else ""


def _parse_json(text):
    """Parse JSON, including JSON wrapped in a Markdown code fence."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Recover a JSON object if the model added text around it.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


def _choose_question_type(order):
    """
    Cycle through question types to encourage a balanced mix.
    order is expected to start at 1.
    """
    index = max(0, int(order) - 1) % len(QUESTION_TYPES)
    return QUESTION_TYPES[index]


def _normalize_question(text):
    """Normalize question text for duplicate detection."""
    text = str(text or "").casefold()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_duplicate_question(candidate, previous_questions):
    """Reject exact repeats and very similar questions."""
    normalized = _normalize_question(candidate)
    if not normalized:
        return True

    for old_question in previous_questions:
        old = _normalize_question(old_question)
        if not old:
            continue
        if normalized == old:
            return True

        # Similarity catches minor rewrites of the same question.
        ratio = SequenceMatcher(None, normalized, old).ratio()
        if ratio >= 0.82:
            return True

        # Catch substantial shared wording for longer questions.
        candidate_words = set(normalized.split())
        old_words = set(old.split())
        if len(candidate_words) >= 7 and len(old_words) >= 7:
            overlap = len(candidate_words & old_words) / max(1, len(candidate_words | old_words))
            if overlap >= 0.72:
                return True
    return False


def _fallback_question(question_type, previous_questions, role='this role'):
    """Choose a fallback that has not already been asked."""
    candidates = FALLBACK_QUESTIONS.get(
        question_type, FALLBACK_QUESTIONS["short_answer"]
    )
    unused = [
        question for question in candidates
        if not _is_duplicate_question(question["text"], previous_questions)
    ]

    # Prefer a genuinely new question. If this type's bank is exhausted,
    # search the other types before returning a duplicate.
    if not unused:
        unused = [
            question
            for other_type, questions in FALLBACK_QUESTIONS.items()
            for question in questions
            if not _is_duplicate_question(question["text"], previous_questions)
        ]
        if unused:
            selected = random.choice(unused)
            selected_type = next(
                (kind for kind, questions in FALLBACK_QUESTIONS.items()
                 if selected in questions),
                question_type,
            )
            return {**selected, "question_type": selected_type}

    if unused:
        selected = random.choice(unused)
        return {**selected, "question_type": question_type}

    # A final guard for very long interviews when every built-in fallback
    # has been used: create a role-specific prompt instead of repeating text.
    suffix = len(previous_questions) + 1
    selected = {
        "text": (
            f"For the role of {role}, describe a new practical problem-solving approach for task {suffix}, "
            "including trade-offs and edge cases."
        ),
        "options": [],
        "correct_answer": "State the problem, explain a sound approach, consider edge cases, and justify trade-offs.",
        "skill": "Problem Solving",
        "explanation": "A structured explanation makes technical reasoning easier to assess.",
        "hint": "Break the problem into steps and discuss trade-offs.",
        "question_type": "scenario",
    }
    return selected


def generate_question_data(interview, order, previous_questions=None):
    """
    Generate a structured interview question that avoids repeats in this interview.
    Returns a dictionary compatible with InterviewQuestion.
    """
    previous_questions = list(previous_questions or [])
    question_type = _choose_question_type(order)
    fallback = _fallback_question(question_type, previous_questions, interview.role)
    llm = _get_llm()

    if not llm:
        return {**fallback, "difficulty": interview.difficulty}

    previous_text = "\n".join(
        f"- {str(question)[:500]}" for question in previous_questions[-40:]
    ) or "- None"

    prompt = f"""
Create exactly one original mock interview question as valid JSON.

Candidate target role: {interview.role}
Experience level: {interview.level}
Difficulty: {interview.difficulty}
Required question type: {question_type}
Job description: {interview.job_description[:1200] or "Not provided"}
Resume profile: {_resume_text(interview)[:2000] or "Not provided"}

Questions already asked in THIS interview (do not repeat or paraphrase them):
{previous_text}

Return one JSON object with these keys:
{{
  "text": "The question shown to the candidate",
  "options": ["Option A", "Option B"],
  "correct_answer": "Expected answer, or empty string if not applicable",
  "skill": "Short skill name",
  "explanation": "Why the expected answer is correct",
  "hint": "A helpful hint that does not reveal the answer"
}}

Rules:
- The question type must be exactly "{question_type}".
- Ask about a different concept, task, example, or scenario from all prior questions.
- Do not simply change names or wording in a previously asked question.
- For mcq, provide 4 distinct options and set correct_answer to the exact text of one option.
- For true_false, options must be ["True", "False"] and correct_answer must be "True" or "False".
- For short_answer, coding, debugging and scenario, use an empty options list.
- For coding, ask a clear programming task and provide a concise expected solution description.
- For debugging, include the code or error to investigate in the question.
- For scenario, describe a realistic situation relevant to the target role.
- Do not invent details about the candidate's resume.
- Return JSON only. Do not use Markdown fences.
"""

    # Retry once if Groq returns malformed or repeated content.
    last_error = None
    for attempt in range(2):
        try:
            active_prompt = prompt
            if attempt:
                active_prompt += (
                    "\nIMPORTANT RETRY: The previous generated question was invalid "
                    "or too similar to an earlier one. Generate a substantially "
                    "different question about another concept. JSON only."
                )

            result = _content_to_text(llm.invoke(active_prompt).content)
            data = _parse_json(result)
            if not isinstance(data, dict):
                raise ValueError("Groq did not return a valid JSON object.")

            text = str(data.get("text", "")).strip()
            if not text:
                raise ValueError("Generated question text is empty.")
            if _is_duplicate_question(text, previous_questions):
                raise ValueError("Generated question repeats or closely resembles a previous question.")

            options = data.get("options", [])
            if not isinstance(options, list):
                options = []
            options = [str(option).strip() for option in options if str(option).strip()]
            correct_answer = str(data.get("correct_answer", "")).strip()

            if question_type == "mcq":
                if len(options) != 4 or len({_normalize_question(o) for o in options}) != 4:
                    raise ValueError("Generated MCQ must contain four distinct options.")
                if correct_answer not in options:
                    raise ValueError("Generated MCQ correct answer must match one option.")

            if question_type == "true_false":
                if correct_answer.casefold() not in {"true", "false"}:
                    raise ValueError("Generated True/False answer is invalid.")
                options = ["True", "False"]
                correct_answer = correct_answer.capitalize()

            return {
                "text": text[:4000],
                "question_type": question_type,
                "options": options,
                "correct_answer": correct_answer[:4000],
                "skill": str(data.get("skill") or interview.role)[:100],
                "explanation": str(data.get("explanation", ""))[:4000],
                "hint": str(data.get("hint", ""))[:1000],
                "difficulty": interview.difficulty,
            }

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Question generation attempt %s failed: %s",
                attempt + 1, exc,
            )

    logger.warning("Using non-repeating fallback question after Groq failures: %s", last_error)
    return {**fallback, "difficulty": interview.difficulty}


def generate_question(interview, order, previous_questions):
    """
    Backward-compatible wrapper for the existing views.py.

    Existing code expects: text, question_type = generate_question(...)
    """
    data = generate_question_data(interview, order, previous_questions)
    return data["text"], data["question_type"]


def _normalize_answer(value):
    """Normalize an answer for basic objective-answer comparison."""
    value = str(value or "").strip().casefold()
    value = re.sub(r"^\s*(?:option\s*)?([a-d])\s*[\.\):\-]\s*", r"\1 ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n.!?")


def _evaluate_objective(question, answer):
    """Score MCQ and True/False answers deterministically."""
    correct = str(question.correct_answer or "").strip()
    submitted = str(answer or "").strip()
    options = question.options if isinstance(question.options, list) else []

    if question.question_type == "mcq":
        # Allow the candidate to submit either the option text or A/B/C/D.
        if submitted.upper() in {"A", "B", "C", "D"}:
            index = ord(submitted.upper()) - ord("A")
            if index < len(options):
                submitted = str(options[index])

    if question.question_type == "true_false":
        aliases = {
            "t": "true",
            "yes": "true",
            "f": "false",
            "no": "false",
        }
        submitted = aliases.get(submitted.casefold(), submitted).capitalize()
        correct = correct.capitalize()

    is_correct = (
        bool(submitted)
        and bool(correct)
        and _normalize_answer(submitted) == _normalize_answer(correct)
    )

    explanation = question.explanation.strip()
    if is_correct:
        feedback = "Correct answer."
        if explanation:
            feedback += " " + explanation
        score = 10
    elif not submitted:
        feedback = "No answer was submitted."
        if explanation:
            feedback += " " + explanation
        score = 0
    else:
        feedback = f"Not quite. The expected answer is: {correct}."
        if explanation:
            feedback += " " + explanation
        score = 0

    return {
        "score": score,
        "topic": question.skill or "General",
        "key_points": correct or "Review the question and its relevant concept.",
        "ideal_answer": correct,
        "improvement_areas": (
            "Review the concept and explanation, then try a similar question."
            if not is_correct
            else "Keep practising to reinforce this concept."
        ),
        "feedback": feedback,
    }


def evaluate_answer(interview, question, answer, elapsed_seconds):
    """
    Evaluate objective questions locally and descriptive questions with Groq.

    Return keys are compatible with the existing submit_answer view, with
    ideal_answer and improvement_areas included for the report template.
    """
    answer = (answer or "").strip()

    if question.question_type in {"mcq", "true_false"}:
        return _evaluate_objective(question, answer)

    fallback = {
        "score": 5 if answer else 0,
        "topic": question.skill or "General",
        "key_points": (
            question.correct_answer
            or "Answer directly, explain your reasoning, and give a relevant example."
        ),
        "ideal_answer": (
            question.correct_answer
            or "Start with a direct answer, explain the reasoning, and give a relevant example."
        ),
        "improvement_areas": (
            "Be specific, explain why your approach works, and include a concrete example."
        ),
        "feedback": (
            "Your response has been recorded. Add relevant detail and explain your reasoning."
            if answer
            else "No answer was provided. Try to attempt every question."
        ),
    }

    llm = _get_llm()
    if not llm:
        return fallback

    prompt = f"""
Evaluate this mock interview answer fairly and constructively.

Target role: {interview.role}
Experience level: {interview.level}
Difficulty: {interview.difficulty}
Question type: {question.question_type}
Skill assessed: {question.skill}
Resume profile: {_resume_text(interview)[:1500] or "Not provided"}
Question: {question.text[:2500]}
Expected answer or rubric: {question.correct_answer[:2500] or "Use a reasonable role-specific rubric."}
Candidate answer: {answer[:5000] or "[No answer]"}
Time limit: {interview.seconds_per_question} seconds
Elapsed time: {elapsed_seconds} seconds

Score from 0 to 10 based on correctness, reasoning, clarity and completeness.
For coding/debugging questions, consider the algorithm, edge cases and explanation.
Do not claim code was executed. Do not invent candidate experience.
Give useful feedback even when the answer is incorrect.

Return exactly one valid JSON object with these keys:
{{
  "score": 0,
  "topic": "short topic",
  "key_points": "important elements of a strong answer",
  "ideal_answer": "concise example answer or solution approach",
  "improvement_areas": "two or three specific improvements",
  "feedback": "specific constructive feedback"
}}
Return JSON only, without Markdown fences.
"""

    try:
        result = _content_to_text(llm.invoke(prompt).content)
        data = _parse_json(result)

        if not isinstance(data, dict):
            raise ValueError("Groq did not return valid evaluation JSON.")

        try:
            score = int(data.get("score", fallback["score"]))
        except (TypeError, ValueError):
            score = fallback["score"]

        return {
            "score": max(0, min(10, score)),
            "topic": str(data.get("topic") or fallback["topic"])[:120],
            "key_points": str(data.get("key_points") or fallback["key_points"]),
            "ideal_answer": str(data.get("ideal_answer") or fallback["ideal_answer"]),
            "improvement_areas": str(
                data.get("improvement_areas") or fallback["improvement_areas"]
            ),
            "feedback": str(data.get("feedback") or fallback["feedback"]),
        }

    except Exception:
        logger.exception("Groq answer evaluation failed; using fallback")
        return fallback
