from flask import Flask, request, session, render_template, redirect, url_for
from questions import flashcards

app = Flask(__name__)
app.secret_key = "your-secret-key"

# ------------------------
# ROUTES
# ------------------------

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/page2', methods=['GET', 'POST'])
def page2():
    return render_template("page2.html")

@app.route('/person', methods=['POST'])
def person():
    uploaded_file = request.files.get("userfile")
    notes_text = request.form.get("notes", "").strip()

    if uploaded_file and uploaded_file.filename != "":
        session["file_text"] = uploaded_file.read().decode("utf-8")
    elif notes_text:
        session["file_text"] = notes_text
    else:
        session["file_text"] = ""

    # Redirect to ghost selection page
    return redirect(url_for('person_select'))  # create a new route for ghost selection

# New route for ghost selection page
@app.route('/person_select')
def person_select():
    return render_template("person.html")

@app.route('/game')
def game():
    notes_text = session.get("file_text", "").strip()
    if not notes_text:
        return "Error: No notes/text found. Go back and provide a file or type notes."

    flashcard_df = flashcards(notes_text)

    return render_template("game.html", flashcard_df=flashcard_df)

if __name__ == "__main__":
    app.run(debug=True)
