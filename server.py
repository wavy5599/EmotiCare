import openai  # Import the OpenAI library to use the GPT chat models
import os  # Import OS to access environment variables
from dotenv import load_dotenv  # Load .env file containing API keys
from flask import Flask, request, jsonify  # Flask modules to create endpoints and handle JSON
from flask_cors import CORS  # Enables CORS for frontend-backend communication
import uuid  # Used for generating anonymous session IDs
import datetime  # Used to timestamp session messages

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)  # Initialize the Flask app
CORS(app)  # Enable CORS so the frontend can talk to the backend

# Set API keys and credentials from environment variables
openai.api_key = os.getenv('api')  # OpenAI API key
FRONTEND_PASSWORD = os.getenv('FRONTEND_PASSWORD')  # Password to authenticate frontend
guest_key = os.getenv('guest_key')  # Guest key placeholder for anonymous access

# Define keywords that should trigger therapist escalation
CRISIS_KEYWORDS = ["suicide", "kill myself", "hurt myself", "end it all", "overdose", "I'm done"]

# Temporary in-memory session storage (use a database for production)
sessions = {}

# Home route to verify server is up
@app.route('/')
def home():
    return "EmotiCare Flask server is live!"  # Health check response

# Route to verify frontend credentials
@app.route('/validate-password', methods=['POST'])
def validate_password():
    data = request.get_json()  # Get the JSON payload from request
    submitted_password = data.get('password')  # Extract submitted password
    if submitted_password == FRONTEND_PASSWORD:
        return jsonify({"success": True})  # Password matches
    return jsonify({"success": False}), 403  # Unauthorized if password incorrect

# Main chat endpoint
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()  # Parse request body
    user_message = data.get("message")  # Extract user message
    session_id = data.get("session_id", str(uuid.uuid4()))  # Generate session ID if not provided
    language = data.get("language", "English")  # Optional language support

    # Reject empty messages
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Check for crisis-related keywords
    crisis_triggered = any(kw in user_message.lower() for kw in CRISIS_KEYWORDS)
    if crisis_triggered:
        # Return escalation response to frontend
        return jsonify({
            "reply": (
                "I care about you. It sounds like you might be in crisis. "
                "Please consider calling 988 or contacting a licensed therapist. "
                "Would you like me to help connect you with someone now?"
            ),
            "escalate": True
        })

    try:
        # Send message to OpenAI GPT-4o model
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # GPT-4o model for advanced conversational ability
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are EmotiCare, an empathetic mental health assistant. "
                        "Provide emotional support, validate feelings, and help users gently. "
                        "If the user is struggling, you may offer breathing exercises, journaling, or positive reframing."
                    )
                },
                {"role": "user", "content": user_message}  # Pass user message
            ]
        )

        # Extract assistant's response
        bot_reply = response["choices"][0]["message"]["content"]

        # Store the exchange in the session log
        now = datetime.datetime.utcnow()
        if session_id not in sessions:
            sessions[session_id] = []  # Create session entry
        sessions[session_id].append({"timestamp": now.isoformat(), "user": user_message, "bot": bot_reply})

        return jsonify({"reply": bot_reply, "session_id": session_id})  # Send response and session ID back

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Handle any runtime errors

# Route to retrieve previous session by session_id
@app.route('/get-session/<session_id>', methods=['GET'])
def get_session(session_id):
    session_data = sessions.get(session_id)  # Look up session data
    if not session_data:
        return jsonify({"error": "Session not found"}), 404  # If not found
    return jsonify(session_data)  # Return chat history

# Route to simulate saving session to a file or storage
@app.route('/save-session', methods=['POST'])
def save_session():
    data = request.get_json()  # Parse request
    session_id = data.get("session_id")  # Session to save
    export = data.get("export")  # Mock export content
    return jsonify({"message": f"Session {session_id} saved (mock response).", "export": export})

# Endpoint to notify therapist if user is in crisis
@app.route('/alert-therapist', methods=['POST'])
def alert_therapist():
    data = request.get_json()  # Get request payload
    session_id = data.get("session_id")  # Affected session
    latest_message = data.get("message")  # Message that triggered the alert
    print(f"[ALERT] Therapist notified: Session {session_id} flagged for review.")  # Log alert
    return jsonify({"alert": "Therapist notified successfully."})  # Confirmation to frontend

# Endpoint to allow therapist to send a message to a session
@app.route('/therapist-reply', methods=['POST'])
def therapist_reply():
    data = request.get_json()  # Parse request
    session_id = data.get("session_id")  # Identify session
    reply_message = data.get("reply")  # Therapist's message

    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404  # Return error if session doesn't exist

    # Append therapist message to the session
    now = datetime.datetime.utcnow()
    sessions[session_id].append({"timestamp": now.isoformat(), "therapist": reply_message})
    return jsonify({"message": "Therapist message stored."})  # Return confirmation

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)  # Run on all network interfaces, port 5000
