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

@app.route('/game', methods=['POST'])
def game():
    # File comes from the form
    uploaded = request.files.get('userfile')

    if not uploaded:
        return "No file uploaded", 400

    # Save file temporarily
    filename = str(uuid.uuid4()) + ".txt"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    uploaded.save(filepath)

    # Store path for loading() to read
    session['filepath'] = filepath

    # Go to loading screen
    return redirect(url_for('loading'))


@app.route('/loading', methods=['GET'])
def loading():
    filepath = session.get('filepath')

    if not filepath:
        return "File path missing", 400

    # Compute results
    flashcard_data = flashcards(filepath)
    quiz_data = quiz(flashcard_data)

    # Show game page
    return render_template(
        "game.html",
        flashcard_df=flashcard_data,
        quiz_df=quiz_data
    )

@app.route('/person', methods=['GET'])
def person():
    return render_template("person.html")

app.run(host='0.0.0.0', port=8080)
