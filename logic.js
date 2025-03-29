// Updated logic.js with typing animation integration and comments


let userName = '';
let userAge = '';
let userEmail = '';
let userReason = '';


const app = document.getElementById('app'); // Get reference to the app container
let messages = []; // Store chat messages
let mood = null; // Store user mood
let sessionId = null; // Store session ID from backend

// Render the initial form for user input
function renderIntroForm() {
  app.innerHTML = `
  <div class="intro-wrapper">
    <img class="logo" src="/assets/logo.png" alt="EmotiCare Logo" />
    <div class="intro-form">
      <h2 class="intro-heading">Before we begin...</h2>
      <form onsubmit="startSession(event)">
        <input id="nameInput" placeholder="Your name (optional)" />
        <input id="ageInput" type="number" placeholder="Your age (optional)" />
        <input id="emailInput" type="email" placeholder="Your email (optional)" />
        <textarea id="reasonInput" placeholder="What's on your mind today?" required></textarea>
        <button type="submit">Continue</button>
        <p class="terms-text">
          By continuing, you agree to our
          <a href="/terms-service.html" target="_blank">Terms of Service</a>.
        </p>
      </form>
    </div>
  </div>
  `;
}

// Handle form submission and start session
async function startSession(event) {
  event.preventDefault();
  const name = document.getElementById('nameInput').value;
const age = document.getElementById('ageInput').value;
const reason = document.getElementById('reasonInput').value;
const email = document.getElementById('emailInput').value;

userName = name;
userAge = age;
userEmail = email;
userReason = reason;


  // Send session start to backend
  const res = await fetch('http://localhost:5000/start-session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, age, reason, email })
  });

  const data = await res.json();
  sessionId = data.session_id;

  // Send user session info via Web3Forms
  const web3formPayload = {
    access_key: "ba6ae6bd-3d82-4477-b7f2-d54fb5e69547",
    name,
    email,
    subject: "New EmotiCare Session",
    message: `Name: ${name || 'Anonymous'}\nAge: ${age || 'N/A'}\nReason: ${reason}`
  };

  await fetch("https://api.web3forms.com/submit", {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, age, reason, email })
  });

  renderMoodSelector(); // Show mood selector after form
}
async function sendToDoctor() {
  const input = document.getElementById('userInput');
  const userText = input.value.trim();

  if (!userText) {
    alert("Please enter a message before sending.");
    return;
  }

  const payload = {
    access_key: "ba6ae6bd-3d82-4477-b7f2-d54fb5e69547",
    subject: "User Chat Message to Therapist",
    name: userName,
    email: userEmail,
    message: `
🧠 New Message from EmotiCare:

Name: ${userName || 'Anonymous'}
Age: ${userAge || 'N/A'}
Email: ${userEmail || 'Not Provided'}

Initial Concern:
${userReason || 'Not Provided'}

User's Message:
"${userText}"
    `.trim()
  };

  try {
    const response = await fetch("https://api.web3forms.com/submit", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    if (result.success) {
      alert("Message successfully sent to the therapist.");
      input.value = ''; // Clear the input box
    } else {
      alert("Failed to send message. Please try again.");
    }
  } catch (err) {
    alert("Error sending message to the therapist.");
    console.error(err);
  }
}

// Render mood selection screen
function renderMoodSelector() {
  app.innerHTML = `
    <div class="mood-selector">
      <h2>How are you feeling today?</h2>
      <div class="moods">
        ${["😊", "😐", "😢", "😠"].map(m => `<button onclick="selectMood('${m}')">${m}</button>`).join('')}
      </div>
    </div>
  `;
}

// Handle mood selection and start conversation
function selectMood(selectedMood) {
  mood = selectedMood;
  messages.push({ sender: 'bot', text: `Hey there 👋 I see you're feeling ${mood}. I'm here for you. If there is anything you want to talk about today!` });
  renderChat();
}

// Render chat UI and tools
function renderChat() {
  app.innerHTML = `
    <div class="chat-container" id="chat-container">
      ${messages.map(msg =>
        msg.typing
          ? `<div class="message bot"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`
          : `<div class="message ${msg.sender}" style="white-space: pre-wrap; line-height: 1.5;">${msg.text}</div>`
      ).join('')}
    </div>
    <div class="tools">
      <button onclick="addTool('breathing')">🧘 Breathe</button>
      <button onclick="addTool('journal')">📝 Journal</button>
    </div>
    <form class="input-area" onsubmit="sendMessage(event)">
      <textarea id="userInput" class="input-modern" placeholder="Type something you're feeling..." autocomplete="off" rows="1" oninput="autoExpand(this)"></textarea>
      <button type="submit">Send to 🤖</button>
      <button type="button" onclick="sendToDoctor()">Send to 👨‍⚕️</button>
    </form>
  `;
  const chatContainer = document.getElementById('chat-container');
  chatContainer.scrollTop = chatContainer.scrollHeight; // Auto-scroll to bottom
}

// Handle user message sending
async function sendMessage(event) {
  event.preventDefault();
  const input = document.getElementById('userInput');
  const userText = input.value.trim();
  if (!userText) return;

  messages.push({ sender: 'user', text: userText });
  renderChat();
  input.value = '';

  messages.push({ sender: 'bot', typing: true });
  renderChat();

  try {
    const res = await fetch('http://localhost:5000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userText, session_id: sessionId })
    });

    const data = await res.json();
    console.log("API Response:", data); // <-- DEBUG LOG

    const botReply = data.reply || data.message || "Sorry, I didn't understand that.";
    messages = messages.filter(msg => !msg.typing);
    messages.push({ sender: 'bot', text: botReply });
  } catch (err) {
    messages = messages.filter(msg => !msg.typing);
    messages.push({ sender: 'bot', text: 'Sorry, something went wrong.' });
  }

  renderChat();
}

// Toggle between dark and light mode
function toggleMode() {
  document.body.classList.toggle('light-mode');
}

// Add breathing or journal tool responses
function addTool(tool) {
  const journalPrompts = [
    "What is one thing you’re grateful for today, and why?",
    "Describe a moment recently when you felt truly at peace.",
    "Write a letter to your future self a year from now.",
    "What's something you're proud of that others may not know?",
    "What would you say to your younger self today?"
  ];

  const breathingExercises = [
    "Inhale deeply for 4 seconds, hold for 4, exhale for 4 — repeat this 3 times.",
    "Try box breathing: inhale 4 sec, hold 4 sec, exhale 4 sec, hold 4 sec.",
    "Breathe in through your nose, out through your mouth, slowly and deeply.",
    "Focus on your breath. Count 1 on the inhale, 2 on the exhale. Go to 10 and repeat.",
    "Breathe in: 'I am calm'. Breathe out: 'I release tension.' Repeat 5 times."
  ];

  // Select random prompt or exercise
  if (tool === 'breathing') {
    const randomBreathing = breathingExercises[Math.floor(Math.random() * breathingExercises.length)];
    messages.push({ sender: 'bot', text: randomBreathing });
  } else if (tool === 'journal') {
    const randomPrompt = journalPrompts[Math.floor(Math.random() * journalPrompts.length)];
    messages.push({ sender: 'bot', text: randomPrompt });
  }

  renderChat();
}

// Auto-expand textarea height as user types
function autoExpand(field) {
  field.style.height = 'inherit';
  const computed = window.getComputedStyle(field);
  const height = parseInt(computed.getPropertyValue('border-top-width'), 10)
               + parseInt(computed.getPropertyValue('padding-top'), 10)
               + field.scrollHeight
               + parseInt(computed.getPropertyValue('padding-bottom'), 10)
               + parseInt(computed.getPropertyValue('border-bottom-width'), 10);
  field.style.height = `${height}px`;
}

// Initialize the app with intro form
renderIntroForm();
