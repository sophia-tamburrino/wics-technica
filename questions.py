import ollama
import pandas as pd
import re

def flashcards(path):
    #path will be a txt file.
    print("PATH: ", path)
    notes = path
    df = pd.DataFrame(columns=["question", "answer"])
    print("Generating 1")
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

        Repeat and make 4 total flashcards to help this user study. Do not disobey the format and do not add any additional text other than the flashcards.

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

def quiz(original_df):

    df = pd.DataFrame(columns=["Option 1", "Option 2", "Option 3", "Option 4", "Answer Key"])
    print("Generating 2")
    prompt = f"""
        You are an AI assistant meant to generate a quiz from a user's imported flashcards. Here are the flashcards:

        {original_df}
        
        Your task:
        
        Generate a 5-question multiple-choice quiz in this format- 
        **Question 1**
        "OPTION 1:" <Possible answer>
        "OPTION 2:" <Possible answer>
        "OPTION 3:" <Possible answer>
        "OPTION 4:" <Possible answer>
        "CORRECT ANSWER:" <Option number with the correct answer>

        Repeat for 5 questions to help this user study. Do not disobey the format and do not add any additional text other than the quiz.

    """

    try:
        # generate response from llama
        model_response = ollama.generate(model='llama3.2:3b', prompt=prompt)
        raw_response = model_response.get('response', '').strip()
        print(raw_response)
        #its annoying so we need to use regex.
        
        # Each 
        pattern1 = r'OPTION 1:\s*(.*)'
        option1 =  re.findall(pattern1, raw_response)
        print(option1)

        pattern2 = r'OPTION 2:\s*(.*)'
        option2 =  re.findall(pattern2, raw_response)
        print(option2)

        pattern3 = r'OPTION 3:\s*(.*)'
        option3 =  re.findall(pattern3, raw_response)
        print(option3)

        pattern4 = r'OPTION 4:\s*(.*)'
        option4 =  re.findall(pattern4, raw_response)
        print(option4)
       
        answers = r'CORRECT ANSWER:\s*(.*)'
        answerkey =  re.findall(answers, raw_response)
        print(answerkey)

        df = pd.DataFrame({
            'Option 1' : option1,
            'Option 2' : option2,
            'Option 3' : option3,
            'Option 4' : option4,
            'Answer Key' : answerkey,
        })

    except Exception as e:
        print("ERROR", e)

    print("Final:", df)
    return df

