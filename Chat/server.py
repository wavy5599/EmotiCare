import openai  # OpenAI GPT chat models
import os  # Access environment variables
from dotenv import load_dotenv  # Load .env variables
from flask import Flask, request, jsonify  # Flask web server and JSON response
from flask_cors import CORS  # Cross-origin support for frontend
import uuid  # Unique session IDs
import datetime  # Timestamps
import smtplib  # Sending emails
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Initialize app and enable CORS
app = Flask(__name__)
CORS(app)

# API keys from .env
openai.api_key = os.getenv('api')
FRONTEND_PASSWORD = os.getenv('FRONTEND_PASSWORD')
guest_key = os.getenv('guest_key')

# Keywords that trigger escalation
CRISIS_KEYWORDS = ["suicide", "kill myself", "hurt myself", "end it all", "overdose", "I'm done", "drugs"]

# In-memory session store
sessions = {}

# Email handler function
def send_emails(name, age, user_email, reason):
    sender = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASS')
    therapist_email = os.getenv('THERAPIST_EMAIL')

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)

        # Therapist email
        therapist_msg = MIMEMultipart()
        therapist_msg['From'] = sender
        therapist_msg['To'] = therapist_email
        therapist_msg['Subject'] = f"New EmotiCare Session from {name or 'Anonymous'}"
        therapist_body = f"""
        A user has started a new session:

        Name: {name or 'Anonymous'}
        Age: {age or 'N/A'}
        Email: {user_email or 'Not provided'}
        Reason for Reaching Out: {reason}
        """
        therapist_msg.attach(MIMEText(therapist_body, 'plain'))
        server.send_message(therapist_msg)

        # User confirmation email
        if user_email:
            user_msg = MIMEMultipart()
            user_msg['From'] = sender
            user_msg['To'] = user_email
            user_msg['Subject'] = "Welcome to EmotiCare 💙"

            user_body = f"""
            Hi {name or 'there'},

            Thank you for reaching out to EmotiCare. We're here to support you.
            A licensed therapist may review your session and follow up if needed.

            In the meantime, feel free to explore helpful exercises and continue chatting.

            – EmotiCare Team
            """
            user_msg.attach(MIMEText(user_body, 'plain'))
            server.send_message(user_msg)

        server.quit()
        print("[INFO] Emails sent to therapist and user.")

    except Exception as e:
        print(f"[ERROR] Failed to send emails: {e}")

# Home route
@app.route('/')
def home():
    return "EmotiCare Flask server is live!"

# Password validation
@app.route('/validate-password', methods=['POST'])
def validate_password():
    data = request.get_json()
    if data.get('password') == FRONTEND_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False}), 403

# Start session
@app.route('/start-session', methods=['POST'])
def start_session():
    data = request.get_json()
    session_id = str(uuid.uuid4())
    name = data.get("name", "Anonymous")
    age = data.get("age", "N/A")
    reason = data.get("reason", "Not specified")
    email = data.get("email", "")

    sessions[session_id] = [{
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "intro": {
            "name": name,
            "age": age,
            "reason": reason,
            "email": email
        }
    }]

    send_emails(name, age, email, reason)

    return jsonify({"session_id": session_id})

# Chat handler
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message")
    session_id = data.get("session_id", str(uuid.uuid4()))

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    if any(kw in user_message.lower() for kw in CRISIS_KEYWORDS):
        return jsonify({
            "reply": (
                "I care about you. It sounds like you might be in crisis. "
                "Please consider calling 988 or contacting a licensed therapist. "
                "Would you like me to help connect you with someone now?"
            ),
            "escalate": True
        })

    try:
        intro = sessions.get(session_id, [{}])[0].get("intro", {})
        system_prompt = (
            f"You are EmotiCare, an empathetic mental health assistant.\n"
            f"User Name: {intro.get('name', 'Anonymous')}\n"
            f"User Age: {intro.get('age', 'N/A')}\n"
            f"User Reason for Chat: {intro.get('reason', 'Not specified')}\n\n"
            "Provide emotional support, validate feelings, and help users gently. "
            "If the user is struggling, you may offer breathing exercises, journaling, or positive reframing."
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )

        bot_reply = response["choices"][0]["message"]["content"]

        now = datetime.datetime.utcnow()
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append({"timestamp": now.isoformat(), "user": user_message, "bot": bot_reply})

        return jsonify({"reply": bot_reply, "session_id": session_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get session history
@app.route('/get-session/<session_id>', methods=['GET'])
def get_session(session_id):
    session_data = sessions.get(session_id)
    if not session_data:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session_data)

# Mock save session
@app.route('/save-session', methods=['POST'])
def save_session():
    data = request.get_json()
    session_id = data.get("session_id")
    export = data.get("export")
    return jsonify({"message": f"Session {session_id} saved (mock response).", "export": export})

# Crisis alert to therapist
@app.route('/alert-therapist', methods=['POST'])
def alert_therapist():
    data = request.get_json()
    session_id = data.get("session_id")
    message = data.get("message")
    print(f"[ALERT] Therapist notified: Session {session_id} flagged for review.")
    return jsonify({"alert": "Therapist notified successfully."})

# Therapist manual reply
@app.route('/therapist-reply', methods=['POST'])
def therapist_reply():
    data = request.get_json()
    session_id = data.get("session_id")
    reply = data.get("reply")

    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    now = datetime.datetime.utcnow()
    sessions[session_id].append({"timestamp": now.isoformat(), "therapist": reply})
    return jsonify({"message": "Therapist message stored."})

# Start server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)