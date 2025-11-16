# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import re 
# ✅ NEW: import our Ollama-based generator
from questions import flashcards as generate_flashcards_df

app = Flask(__name__)
CORS(app)  # lets the game/frontend call this from another port (e.g. GameMaker HTML)

# ---------------------------------------------------------
# Session management (this is your backend "state")
# ---------------------------------------------------------

class Session:
    def __init__(self, num_lessons: int):
        self.session_id = str(uuid.uuid4())
        self.num_lessons = num_lessons
        self.current_lesson = 1
        self.score = 0
        self.finished = False

SESSIONS = {}  # session_id -> Session object


def create_session(num_lessons: int) -> Session:
    s = Session(num_lessons)
    SESSIONS[s.session_id] = s
    return s


def get_session(session_id: str) -> Session:
    if session_id not in SESSIONS:
        raise KeyError("Invalid session_id")
    return SESSIONS[session_id]


# ---------------------------------------------------------
# ROUTES – the game/frontend will call these
# ---------------------------------------------------------

@app.route("/ping")
def ping():
    return jsonify({"message": "pong"})


@app.route("/start-session", methods=["POST"])
def start_session():
    """
    Body:
    {
      "num_lessons": 3
    }

    Response:
    {
      "session_id": "...",
      "num_lessons": 3
    }
    """
    data = request.get_json() or {}
    num_lessons = int(data.get("num_lessons", 1))

    session = create_session(num_lessons)

    # TODO (AI teammate): optionally generate/store questions/flashcards for this session_id
    return jsonify({
        "session_id": session.session_id,
        "num_lessons": num_lessons
    })


@app.route("/checkpoint", methods=["GET"])
def checkpoint():
    """
    Query params:
      session_id: string
      lesson: int
      checkpoint: int (index of checkpoint in that lesson)

    Response:
    {
      "flashcards": [
        { "front": "...", "back": "..." },
        ...
      ]
    }
    """
    try:
        session_id = request.args.get("session_id")
        lesson = int(request.args.get("lesson", 1))
        checkpoint_idx = int(request.args.get("checkpoint", 0))

        _ = get_session(session_id)  # just to validate session exists

        flashcards = get_flashcards_for_checkpoint(session_id, lesson, checkpoint_idx)
        return jsonify({"flashcards": flashcards})

    except KeyError:
        return jsonify({"error": "Invalid session_id"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/lesson-quiz", methods=["GET"])
def lesson_quiz():
    """
    Query params:
      session_id: string
      lesson: int

    Response:
    {
      "questions": [
        {
          "id": "q1_l1",
          "question": "...",
          "options": ["A","B","C","D"],
          "correct_index": 2
        },
        ...
      ]
    }
    """
    try:
        session_id = request.args.get("session_id")
        lesson = int(request.args.get("lesson", 1))

        _ = get_session(session_id)  # validate

        questions = get_quiz_for_lesson(session_id, lesson)
        return jsonify({"questions": questions})

    except KeyError:
        return jsonify({"error": "Invalid session_id"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/lesson-quiz/submit", methods=["POST"])
def submit_lesson_quiz():
    """
    Body:
    {
      "session_id": "...",
      "lesson": 1,
      "answers": [
        { "id": "q1_l1", "choice": 2 },
        ...
      ]
    }

    Response:
    {
      "correct": X,
      "total": Y,
      "new_score": Z,
      "current_lesson": N
    }
    """
    try:
        data = request.get_json() or {}
        session_id = data["session_id"]
        lesson = int(data["lesson"])
        answers = data.get("answers", [])

        session = get_session(session_id)

        correct, total = check_lesson_quiz_answers(session_id, lesson, answers)

        # simple scoring rule: +10 per correct
        session.score += correct * 10

        # move them forward if they passed this lesson
        if lesson >= session.current_lesson:
            session.current_lesson = lesson + 1

        return jsonify({
            "correct": correct,
            "total": total,
            "new_score": session.score,
            "current_lesson": session.current_lesson
        })

    except KeyError as e:
        msg = str(e)
        if "session_id" in msg:
            return jsonify({"error": "Invalid session_id"}), 400
        return jsonify({"error": "Missing field"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/final-quiz", methods=["GET"])
def final_quiz():
    """
    Query params:
      session_id: string

    Response:
    {
      "questions": [ { ... }, ... ]
    }
    """
    try:
        session_id = request.args.get("session_id")
        _ = get_session(session_id)

        questions = get_final_quiz_questions(session_id)
        return jsonify({"questions": questions})

    except KeyError:
        return jsonify({"error": "Invalid session_id"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/final-quiz/submit", methods=["POST"])
def submit_final_quiz():
    """
    Body:
    {
      "session_id": "...",
      "answers": [
        { "id": "final1", "choice": 1 },
        ...
      ]
    }

    Response:
    {
      "correct": X,
      "total": Y,
      "final_score": Z,
      "won": true/false
    }
    """
    try:
        data = request.get_json() or {}
        session_id = data["session_id"]
        answers = data.get("answers", [])

        session = get_session(session_id)
        correct, total = check_final_quiz_answers(session_id, answers)

        # scoring: final quiz is worth more
        session.score += correct * 20
        session.finished = True

        final_score = session.score
        # define win condition (e.g. >= 70% on final)
        won = (total > 0 and (correct / total) >= 0.7)

        return jsonify({
            "correct": correct,
            "total": total,
            "final_score": final_score,
            "won": won
        })

    except KeyError:
        return jsonify({"error": "Invalid session_id"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# AI-backed helpers (flashcards + quizzes)
# ---------------------------------------------------------
import re  # make sure this is at the top of app.py if it's not already

def get_flashcards_for_checkpoint(session_id: str, lesson: int, checkpoint_idx: int):
    """
    Parse os-notes.txt into flashcards.

    Heuristic:
    - Lines that look like "9/2", "9/4" etc. are dates → used as boundaries.
    - Lines that are non-empty and NOT starting with '*' or '-' are treated as section titles.
    - Bullets under a title belong to that title.
    - Each title + its bullets becomes one flashcard:
        front: the title (maybe prefixed as a question)
        back: all the bullet lines joined.
    """
    try:
        with open("os-notes.txt", "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception as e:
        print("ERROR reading os-notes.txt:", e)
        return [
            {
                "front": "Error reading os-notes.txt",
                "back": str(e),
            }
        ]

    lines = [ln.rstrip() for ln in raw.splitlines()]

    flashcards = []
    current_title = None
    buffer = []

    def flush_card():
        nonlocal current_title, buffer
        if current_title and buffer:
            # make the question a bit more explicit
            front = f"{current_title}"
            back = "\n".join(buffer).strip()
            flashcards.append({"front": front, "back": back})
        current_title = None
        buffer = []

    for line in lines:
        stripped = line.strip()

        # skip totally empty lines
        if not stripped:
            continue

        # date lines like "9/2", "9/4", "11/11", etc. → boundary
        if re.match(r"^\d{1,2}/\d{1,2}$", stripped):
            flush_card()
            continue

        # heading: not a bullet and not an emoji-only line
        if not stripped.startswith("*") and not stripped.startswith("-"):
            # new heading → flush previous card, start new one
            flush_card()
            current_title = stripped
            buffer = []
        else:
            # bullet or detail line → belongs to current_title
            # strip leading bullet markers
            cleaned = stripped.lstrip("*").lstrip("-").strip()
            if not current_title:
                # if we somehow get bullets before a heading, just skip them
                continue
            buffer.append(cleaned)

    # flush last card
    flush_card()

    if not flashcards:
        return [
            {
                "front": "No flashcards parsed from os-notes.txt",
                "back": "Check the note formatting or adjust get_flashcards_for_checkpoint.",
            }
        ]

    return flashcards

def get_quiz_for_lesson(session_id: str, lesson: int):
    # questions are multiple-choice
    # (still dummy for now; can be wired to questions.quiz() later)
    return [
        {
            "id": f"q{lesson}_1",
            "question": f"Dummy question for lesson {lesson}: What is 2 + 2?",
            "options": ["1", "2", "3", "4"],
            "correct_index": 3
        },
        {
            "id": f"q{lesson}_2",
            "question": f"Dummy question 2 for lesson {lesson}: What is 3 + 3?",
            "options": ["5", "6", "7", "8"],
            "correct_index": 1
        }
    ]


def check_lesson_quiz_answers(session_id: str, lesson: int, answers: list):
    questions = get_quiz_for_lesson(session_id, lesson)
    by_id = {q["id"]: q for q in questions}

    correct = 0
    for ans in answers:
        qid = ans.get("id")
        choice = ans.get("choice")
        if qid in by_id and choice == by_id[qid]["correct_index"]:
            correct += 1

    total = len(questions)
    return correct, total


def get_final_quiz_questions(session_id: str):
    # For now, final quiz is just a generic dummy quiz.
    return [
        {
            "id": "final1",
            "question": "Dummy final question: What is the capital of France?",
            "options": ["Berlin", "London", "Paris", "Rome"],
            "correct_index": 2
        },
        {
            "id": "final2",
            "question": "Dummy final question 2: What is 5 * 3?",
            "options": ["15", "10", "8", "20"],
            "correct_index": 0
        }
    ]

def check_final_quiz_answers(session_id: str, answers: list):
    questions = get_final_quiz_questions(session_id)
    by_id = {q["id"]: q for q in questions}

    correct = 0
    for ans in answers:
        qid = ans.get("id")
        choice = ans.get("choice")
        if qid in by_id and choice == by_id[qid]["correct_index"]:
            correct += 1

    total = len(questions)
    return correct, total


# ---------------------------------------------------------
# Run the app
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
