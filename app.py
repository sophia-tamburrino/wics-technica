from flask import Flask, request, session, render_template, redirect, url_for
import uuid
import os
from questions import flashcards, quiz

app = Flask(__name__)
app.secret_key = "string"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

@app.route('/page2', methods=['GET', 'POST'])
def page2():
    return render_template("page2.html")

@app.route('/person', methods=['POST'])
def person():
    """
    Page2 submits the uploaded file OR notes here.
    We store the content in session, but DO NOT run the AI yet.
    """
    uploaded_file = request.files.get("userfile")
    notes = request.form.get("notes")

    if uploaded_file and uploaded_file.filename != "":
        session["file_text"] = uploaded_file.read().decode("utf-8")
    else:
        session["file_text"] = notes
    
    return render_template("person.html")


@app.route('/game', methods=['POST', 'GET'])
def game():
    """
    Person page submits 'Start Game' button → generate flashcards + quiz here.
    """
    text = session.get("file_text", "")

    flashcard_df = flashcards(text)     # generate flashcards
    quiz_df = quiz(flashcard_df)        # generate quiz

    return render_template("game.html",
                           flashcard_df=flashcard_df,
                           quiz_df=quiz_df)


app.run(host='0.0.0.0', port=8080)