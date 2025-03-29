import openai  # OpenAI's API for chat completion
import os  # For accessing environment variables
from dotenv import load_dotenv  # Loads .env file containing API keys and secrets
from flask import Flask, request, jsonify  # Flask for creating the web server and API endpoints
from flask_cors import CORS  # Enables CORS so frontend can talk to backend
import uuid  # For generating unique session IDs
import datetime  # For handling timestamps in session logs

load_dotenv()  # Load environment variables from .env

app = Flask(__name__)  # Initialize Flask app
CORS(app)  # Enable CORS so frontend can communicate without restrictions

openai.api_key = os.getenv('api')  # Set OpenAI API key from environment
FRONTEND_PASSWORD = os.getenv('FRONTEND_PASSWORD')  # Auth password for frontend access
guest_key = os.getenv('guest_key')  # Placeholder for guest login key

# Crisis detection keywords that trigger escalation
CRISIS_KEYWORDS = ["suicide", "kill myself", "hurt myself", "end it all", "overdose", "I'm done"]

# Dictionary to store chat sessions temporarily
sessions = {}

@app.route('/')  # Route for home endpoint

def home():
    return "EmotiCare Flask server is live!"  # Simple message to show server is running

@app.route('/validate-password', methods=['POST'])  # Route to validate frontend password

def validate_password():
    data = request.get_json()  # Parse JSON payload from frontend
    submitted_password = data.get('password')  # Extract submitted password
    if submitted_password == FRONTEND_PASSWORD:  # Check if password matches
        return jsonify({"success": True})  # Return success response
    return jsonify({"success": False}), 403  # Return error if password is incorrect

@app.route('/chat', methods=['POST'])  # Route to handle chat messages

def chat():
    data = request.get_json()  # Parse incoming JSON data
    user_message = data.get("message")  # Extract user's message
    session_id = data.get("session_id", str(uuid.uuid4()))  # Use provided session_id or create a new one
    language = data.get("language", "English")  # Optional language support (default: English)

    if not user_message:
        return jsonify({"error": "Message is required"}), 400  # Return error if no message was sent

    # Check for crisis keywords in the message
    crisis_triggered = any(kw in user_message.lower() for kw in CRISIS_KEYWORDS)
    if crisis_triggered:
        return jsonify({
            "reply": (
                "I care about you. It sounds like you might be in crisis. "
                "Please consider calling 988 or contacting a licensed therapist. "
                "Would you like me to help connect you with someone now?"
            ),
            "escalate": True  # Flag to notify frontend of serious message
        })

    try:
        # Call OpenAI API to generate response
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # Use GPT-4o (Omni) model
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are EmotiCare, an empathetic mental health assistant. "
                        "Provide emotional support, validate feelings, and help users gently. "
                        "If the user is struggling, you may offer breathing exercises, journaling, or positive reframing."
                    )
                },
                {"role": "user", "content": user_message}  # User input
            ]
        )

        bot_reply = response["choices"][0]["message"]["content"]  # Extract chatbot reply

        # Track session messages with timestamp
        now = datetime.datetime.utcnow()
        if session_id not in sessions:
            sessions[session_id] = []  # Create session if not already present
        sessions[session_id].append({"timestamp": now.isoformat(), "user": user_message, "bot": bot_reply})

        return jsonify({"reply": bot_reply, "session_id": session_id})  # Return reply and session ID

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return error if something goes wrong

@app.route('/get-session/<session_id>', methods=['GET'])  # Route to get session history

def get_session(session_id):
    session_data = sessions.get(session_id)  # Retrieve session logs
    if not session_data:
        return jsonify({"error": "Session not found"}), 404  # Return error if not found
    return jsonify(session_data)  # Return session data

@app.route('/save-session', methods=['POST'])  # Route to mock-save session

def save_session():
    data = request.get_json()  # Parse request body
    session_id = data.get("session_id")  # Get session ID to save
    export = data.get("export")  # Optional: Encrypted export data
    # You can encrypt and store this securely in production
    return jsonify({"message": f"Session {session_id} saved (mock response).", "export": export})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)  # Start Flask server on all interfaces at port 5000