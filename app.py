# app.py
from flask import Flask, request, session, render_template, redirect, url_for, request
#from flask_cors import CORS
import uuid
import ollama
import pandas as pd
import re
from questions import flashcards, quiz

app = Flask('app')
#CORS(app)  # lets the game/frontend call this from another port (e.g. GameMaker HTML)
app.debug = True
app.secret_key = "string"

# ---------------------------------------------------------
# ROUTES – the game/frontend will call these
# ---------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
  return render_template("index.html")

@app.route('/page2', methods=['GET', 'POST'])
def page2():
  return render_template("page2.html")

@app.route('/loading', methods=['GET', 'POST'])
def loading():
  return render_template("loading.html")

@app.route('/person', methods=['GET', 'POST'])
def person():
  return render_template("person.html")

@app.route('/game', methods=['GET', 'POST'])
def game():
  if request.method == 'POST':
    file = request.files.get['userfile']
    # Redirect to loading page, and once the dataframes are done developing, pass them into game template
    redirect('loading.html')
    flashcard_data = flashcards(file)
    quiz_data = quiz(flashcard_data)
  return render_template("game.html", flashcard_df = flashcard_data, quiz_df = quiz_data)



# ---------------------------------------------------------
# Run the app
# ---------------------------------------------------------
app.run(host='0.0.0.0', port=8080)
