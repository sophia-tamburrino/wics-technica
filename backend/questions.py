import ollama
import pandas as pd
import re

def flashcards(path):
    """
    Given a text file at `path`, call Ollama and return a DataFrame
    with columns: Questions, Answers
    """
    notes = open(path, "r", encoding="utf-8").read()
    df = pd.DataFrame(columns=["Questions", "Answers"])

    prompt = f"""
You are an AI assistant meant to generate flashcards from a user's imported notes. Here are the user's notes:

{notes}

Your task:

Generate flashcards in this format- 
**Flashcard 1**
QUESTION: <Question>
ANSWER: <Answer>

Repeat and make 10 total flashcards to help this user study. 
Do not disobey the format and do not add any additional text other than the flashcards.
"""

    try:
        model_response = ollama.generate(model="llama3.2:3b", prompt=prompt)
        raw_response = model_response.get("response", "").strip()
        print("RAW OLLAMA RESPONSE:\n", raw_response)

        # grab each QUESTION: line
        questions = re.findall(r"QUESTION:\s*(.*)", raw_response)
        # grab each ANSWER: line
        answers = re.findall(r"ANSWER:\s*(.*)", raw_response)

        print("PARSED QUESTIONS:", questions)
        print("PARSED ANSWERS:", answers)

        df = pd.DataFrame(
            {
                "Questions": questions,
                "Answers": answers,
            }
        )

    except Exception as e:
        print("ERROR generating flashcards:", e)

    print("Final flashcards DF:\n", df)
    return df


def quiz(original_df):
    """
    Given a DataFrame of flashcards, call Ollama to make a 5-question quiz.
    Returns a DataFrame with columns:
    Option 1, Option 2, Option 3, Option 4, Answer Key
    """
    df = pd.DataFrame(
        columns=["Option 1", "Option 2", "Option 3", "Option 4", "Answer Key"]
    )

    prompt = f"""
You are an AI assistant meant to generate a quiz from a user's imported flashcards. Here are the flashcards:

{original_df}

Your task:

Generate a 5-question multiple-choice quiz in this format- 
**Question 1**
OPTION 1: <Possible answer>
OPTION 2: <Possible answer>
OPTION 3: <Possible answer>
OPTION 4: <Possible answer>
CORRECT ANSWER: <Option number with the correct answer>

Repeat for 5 questions to help this user study. 
Do not disobey the format and do not add any additional text other than the quiz.
"""

    try:
        model_response = ollama.generate(model="llama3.2:3b", prompt=prompt)
        raw_response = model_response.get("response", "").strip()
        print("RAW QUIZ RESPONSE:\n", raw_response)

        option1 = re.findall(r"OPTION 1:\s*(.*)", raw_response)
        option2 = re.findall(r"OPTION 2:\s*(.*)", raw_response)
        option3 = re.findall(r"OPTION 3:\s*(.*)", raw_response)
        option4 = re.findall(r"OPTION 4:\s*(.*)", raw_response)
        answerkey = re.findall(r"CORRECT ANSWER:\s*(.*)", raw_response)

        print("OPT1:", option1)
        print("OPT2:", option2)
        print("OPT3:", option3)
        print("OPT4:", option4)
        print("ANS:", answerkey)

        df = pd.DataFrame(
            {
                "Option 1": option1,
                "Option 2": option2,
                "Option 3": option3,
                "Option 4": option4,
                "Answer Key": answerkey,
            }
        )

    except Exception as e:
        print("ERROR generating quiz:", e)

    print("Final quiz DF:\n", df)
    return df


# Optional: only run this for testing if you execute `python questions.py` directly
if __name__ == "__main__":
    df1 = flashcards("/os-notes.txt")
    df2 = quiz(df1)
