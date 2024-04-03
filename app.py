from flask import Flask, request, session, render_template, redirect, url_for, flash
from flask_session import Session
import pandas as pd
import os

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SECRET_KEY"] = "your_secret_key"
Session(app)

# Load questions
df = pd.read_csv('questions.csv', delimiter=';')
print("Column Names:", df.columns)

def save_to_csv(file):
    # Read the uploaded CSV file
    uploaded_df = pd.read_csv(file, delimiter=';')
    # Append the contents of the uploaded file to the existing questions.csv
    combined_df = pd.concat([df, uploaded_df], ignore_index=True)
    # Write the combined DataFrame back to questions.csv
    combined_df.to_csv('questions.csv', index=False, sep=';')

@app.route('/', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        difficulty = request.form.get('difficulty')
        topic = request.form.get('topic')

        # Check if both difficulty and topic are selected
        if not difficulty or not topic:
            flash('Please select both difficulty and topic', 'error')
            return redirect(url_for('quiz'))

        session['difficulty'] = difficulty
        session['topic'] = topic
        session['score'] = 0

        # Filter questions based on selected difficulty and topic
        if 'difficulty' in df.columns and 'topic' in df.columns:
            filtered_questions = df[(df['difficulty'] == difficulty) & (df['topic'] == topic)]
            num_questions = len(filtered_questions)
            if num_questions >= 1:
                sampled_questions = filtered_questions.sample(n=min(20, num_questions), replace=False)
                session['questions'] = sampled_questions.to_dict('records')
                return redirect(url_for('question'))
            else:
                flash(f'No questions found for the selected difficulty ({difficulty}) and topic ({topic})', 'error')
                return redirect(url_for('quiz'))
        else:
            flash("Error: 'difficulty' or 'topic' column not found in questions dataset", 'error')
            return redirect(url_for('quiz'))

    return render_template('quiz.html')



@app.route('/question', methods=['GET', 'POST'])
def question():
    if 'questions' not in session:
        return redirect(url_for('quiz'))
    
    if request.method == 'POST':
        session['user_answers'] = request.form.to_dict()
        return redirect(url_for('result'))
    
    questions_html = ''
    for index, question in enumerate(session['questions']):
        options_html = ''
        for option_key in ['option1', 'option2', 'option3', 'option4']:
            options_html += f'<label><input type="radio" name="q{index}" value="{option_key}"> {question[option_key]}</label><br>'
        questions_html += f"<div><p>{question['question']}</p>{options_html}</div>"
    
    return render_template('question.html', questions_html=questions_html)

@app.route('/result', methods=['GET'])
def result():
    if 'questions' not in session or 'user_answers' not in session:
        return redirect(url_for('quiz'))

    total_questions = len(session['questions'])
    correct_answers = 0
    result_html = ''
    all_questions_html = ''
    
    for index, question in enumerate(session['questions']):
        user_answer_key = session['user_answers'].get(f"q{index}", None)
        correct_answer_key = None
        for option_key in ['option1', 'option2', 'option3', 'option4']:
            if question[option_key] == question.get('correct', None):
                correct_answer_key = option_key
                break

        if user_answer_key is None:
            # If user didn't select any answer
            result_html += f"<div style='color:red;'>Question {index + 1}: Unanswered (0/1). Correct answer: {question[correct_answer_key]}</div>"
            all_questions_html += f"<div>Question {index + 1}: {question['question']}<br> Your answer: <span style='color:red;'>Unanswered</span><br> Correct answer: <span style='color:green;'>{question[correct_answer_key]}</span></div>"
        else:
            if user_answer_key == correct_answer_key:
                # If user's answer is correct
                result_html += f"<div style='color:green;'>Question {index + 1}: Correct! (1/1)</div>"
                correct_answers += 1
                all_questions_html += f"<div>Question {index + 1}: {question['question']}<br> Your answer: <span style='color:green;'>{question[user_answer_key]}</span> (Correct)<br> Correct answer: <span style='color:green;'>{question[correct_answer_key]}</span></div>"
            else:
                # If user's answer is incorrect
                result_html += f"<div style='color:red;'>Question {index + 1}: Incorrect. Your answer: {question[user_answer_key]} | Correct answer: {question[correct_answer_key]} (0/1)</div>"
                all_questions_html += f"<div>Question {index + 1}: {question['question']}<br> Your answer: <span style='color:red;'>{question[user_answer_key]}</span> (Incorrect)<br> Correct answer: <span style='color:green;'>{question[correct_answer_key]}</span></div>"

    score = correct_answers
    session['score'] = score
    score_html = f"<h2>Score: {score}/{total_questions}</h2>"
    
    return render_template('result.html', score_html=score_html, result_html=result_html, all_questions_html=all_questions_html)

@app.route('/quiz', methods=['GET', 'POST'])
def upload_and_return_to_quiz():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            flash('Please select a file', 'error')
            return redirect(url_for('quiz'))
        if file:
            save_to_csv(file)
            flash('File uploaded successfully', 'success')
            return redirect(url_for('quiz'))
    return redirect(url_for('quiz'))  # Redirect to quiz page directly
if __name__ == '__main__':
    app.run(debug=True)
