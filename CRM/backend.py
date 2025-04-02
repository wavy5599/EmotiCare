# app.py (Flask backend for EmotiCare CRM)

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import datetime

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add-lead', methods=['POST'])
def add_lead():
    data = request.get_json()
    name = data.get('name')
    age = data.get('age')
    email = data.get('email')
    reason = data.get('reason')
    mood = data.get('mood')
    session_id = data.get('session_id')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, age, email, reason) VALUES (?, ?, ?, ?)",
                (name, age, email, reason))
    user_id = cur.lastrowid
    cur.execute("INSERT INTO sessions (user_id, session_id, mood, started_at) VALUES (?, ?, ?, ?)",
                (user_id, session_id, mood, datetime.datetime.utcnow()))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Lead added successfully.'})

@app.route('/get-sessions', methods=['GET'])
def get_sessions():
    conn = get_db_connection()
    sessions = conn.execute('''
        SELECT s.session_id, u.name, u.email, u.age, s.mood, s.started_at
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        ORDER BY s.started_at DESC
    ''').fetchall()
    conn.close()

    return jsonify([dict(row) for row in sessions])

@app.route('/add-followup', methods=['POST'])
def add_followup():
    data = request.get_json()
    session_id = data.get('session_id')
    followup_date = data.get('followup_date')
    notes = data.get('notes')

    conn = get_db_connection()
    conn.execute("INSERT INTO followups (session_id, followup_date, notes) VALUES (?, ?, ?)",
                 (session_id, followup_date, notes))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Follow-up added successfully.'})

@app.route('/get-followups', methods=['GET'])
def get_followups():
    conn = get_db_connection()
    followups = conn.execute('SELECT * FROM followups ORDER BY followup_date ASC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in followups])

@app.route('/update-followup', methods=['POST'])
def update_followup():
    data = request.get_json()
    followup_id = data.get('followup_id')
    new_status = data.get('status')

    conn = get_db_connection()
    conn.execute("UPDATE followups SET followup_status = ? WHERE id = ?",
                 (new_status, followup_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Follow-up status updated.'})

if __name__ == '__main__':
    app.run(debug=True)
