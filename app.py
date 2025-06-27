from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import json
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # for session

# Load questions
with open('questions.json') as f:
    questions = json.load(f)


@app.route('/')
def index():
    return redirect(url_for('select_topic'))


@app.route('/select-topic', methods=['GET', 'POST'])
def select_topic():
    if request.method == 'POST':
        selected_topic = request.form['topic']
        # Filter questions by selected topic
        filtered_questions = [q for q in questions if q['topic'] == selected_topic]
        random.shuffle(filtered_questions)
        session['questions'] = filtered_questions
        session['score'] = 0
        session['q_index'] = 0
        return redirect(url_for('quiz'))

    topics = sorted(set(q['topic'] for q in questions))
    return render_template('select_topic.html', topics=topics)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    q_index = session.get('q_index', 0)
    score = session.get('score', 0)
    questions_list = session.get('questions', [])

    if q_index >= len(questions_list):
        return render_template('result.html', score=score, total=len(questions_list))

    if request.method == 'POST':
        selected = request.form.get('option')
        correct = questions_list[q_index - 1]['correct']
        if selected == correct:
            session['score'] += 1

    session['q_index'] += 1
    question = questions_list[q_index]

    return render_template('quiz.html', question=question, index=q_index + 1)


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/questions', methods=['GET'])
def api_questions():
    topic = request.args.get('topic', '').strip().lower()
    if topic:
        filtered = [q for q in questions if q['topic'].lower() == topic]
    else:
        filtered = questions
    random.shuffle(filtered)
    return jsonify(filtered)


if __name__ == '__main__':
    app.run(debug=True)
