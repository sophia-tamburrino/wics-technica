import ollama
import pandas as pd
import re

def flashcards(path):
    #path will be a txt file.
    notes = open(path, "r", encoding="utf-8").read()
    df = pd.DataFrame(columns=["question", "answer"])

    # editing to get llama to generate a response
    # generate prompt for specific dialogue-response pair
    prompt = f"""
        You are an AI assistant meant to generate flashcards from a user's imported notes. Here are the user's notes:

        {notes}
        
        Your task:
        
        Generate flashcards in this format- 
        **Flashcard 1**
        "QUESTION:" <Question>
        "ANSWER:" <Answer>

        Repeat and make 10 total flashcards to help this user study. Do not disobey the format and do not add any additional text other than the flashcards.

    """

    try:
        # generate response from llama
        model_response = ollama.generate(model='llama3.2:3b', prompt=prompt)
        raw_response = model_response.get('response', '').strip()
        print(raw_response)
        #its annoying so we need to use regex.
        # Pattern: matches Flashcard, QUESTION, ANSWER and strips quotes
        pattern1 = r'QUESTION:\s*(.*)'
        questions =  re.findall(pattern1, raw_response)

        pattern2 = r'ANSWER:\s*(.*)'
        answers =  re.findall(pattern2, raw_response)

        print(questions)
        print(answers)
        df = pd.DataFrame({
            'Questions' : questions,
            'Answers' : answers,
        })

    except Exception as e:
        print("ERROR", e)

    print("Final:", df)
    return df

def quiz():
    




flashcards('os-notes.txt') #add path, the user-provided CSV
