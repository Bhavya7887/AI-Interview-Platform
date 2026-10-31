# AI Interview Platform

**Practice Smarter. Interview Better. Grow Faster.**

An AI-powered mock interview platform built with Django and Groq AI. It helps users practice technical interviews, receive automated feedback, evaluate their performance, and improve their skills through personalized learning roadmaps.

## Features

- **AI-Powered Interviews:** Generate dynamic interview questions using Groq AI.
- **Multiple Question Types:** MCQs, True/False, short answers, coding, debugging, and scenario-based questions.
- **Resume-Based Practice:** Upload your resume for interview preparation.
- **Automated Answer Evaluation:** Get AI-powered feedback and answer scores.
- **Performance Reports:** Review interview scores, strengths, and improvement areas.
- **Dashboard:** Track interview history and performance.
- **Learning Roadmaps:** Follow structured learning plans to improve technical skills.
- **Timed Interviews:** Practice answering questions within a time limit.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Django | Web framework |
| Groq AI | AI-powered question generation and evaluation |
| SQLite | Database |
| HTML & CSS | Frontend |
| JavaScript | Interactive functionality |
| Git & GitHub | Version control |

## Project Structure

```text
AI-Interview-Platform/
├── config/
├── interviews/
├── media/
├── static/
├── templates/
├── manage.py
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Bhavya7887/AI-Interview-Platform.git
cd AI-Interview-Platform
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the environment

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root and add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key
```

Never upload your actual API key to GitHub.

### 6. Apply migrations

```bash
python manage.py migrate
```

### 7. Start the development server

```bash
python manage.py runserver
```

Open:

http://127.0.0.1:8000/

## How It Works

1. Register or log in.
2. Create a mock interview.
3. Select your role, experience level, and interview settings.
4. Answer AI-generated questions.
5. Receive automated evaluation and feedback.
6. Review your performance report.
7. Improve using your learning roadmap.

## Future Improvements

- Advanced resume parsing and skill extraction.
- More personalized interview difficulty.
- Improved analytics and performance tracking.
- Additional AI-powered interview modes.

## Author

**Bhavya Sandhu**

- GitHub: [Bhavya7887](https://github.com/Bhavya7887)
- LinkedIn: [Bhavya Sandhu](https://linkedin.com/in/bhavya-sandhu-049673324)

---

*Practice Smarter. Interview Better. Grow Faster.*