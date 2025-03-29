const app = document.getElementById('app');
    let messages = [];
    let mood = null;

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

    function selectMood(selectedMood) {
      mood = selectedMood;
      messages.push({ sender: 'bot', text: `Hey there 👋 I see you're feeling ${mood}. I'm here for you. If there is anything you want to talk about today!` });
      renderChat();
    }

    function renderChat() {
      app.innerHTML = `
        <div class="chat-container" id="chat-container">
          ${messages.map(msg => `<div class="message ${msg.sender}">${msg.text}</div>`).join('')}
        </div>
        <div class="tools">
          <button onclick="addTool('breathing')">🧘 Breathe</button>
          <button onclick="addTool('journal')">📝 Journal</button>
        </div>
        <form class="input-area" onsubmit="sendMessage(event)">
          <input id="userInput" placeholder="Type your message..." />
          <button type="submit">Send</button>
        </form>
      `;
      const chatContainer = document.getElementById('chat-container');
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    async function sendMessage(event) {
      event.preventDefault();
      const input = document.getElementById('userInput');
      const userText = input.value.trim();
      if (!userText) return;
      messages.push({ sender: 'user', text: userText });
      renderChat();
      input.value = '';

      try {
        const res = await fetch('http://localhost:5000/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userText })
        });
        const data = await res.json();
        messages.push({ sender: 'bot', text: data.reply });
      } catch {
        messages.push({ sender: 'bot', text: 'Sorry, something went wrong.' });
      }
      renderChat();
    }

    function toggleMode() {
        document.body.classList.toggle('light-mode');
      }
      

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
      
        if (tool === 'breathing') {
          const randomBreathing = breathingExercises[Math.floor(Math.random() * breathingExercises.length)];
          messages.push({ sender: 'bot', text: randomBreathing });
        } else if (tool === 'journal') {
          const randomPrompt = journalPrompts[Math.floor(Math.random() * journalPrompts.length)];
          messages.push({ sender: 'bot', text: randomPrompt });
        }
        renderChat();
      }
      
      renderMoodSelector();

      // 💬 Updated input field for more modern style
      function renderChat() {
        app.innerHTML = `
          <div class="chat-container" id="chat-container">
            ${messages.map(msg => `<div class="message ${msg.sender}" style="white-space: pre-wrap; line-height: 1.5;">${msg.text}</div>`).join('')}
          </div>
          <div class="tools">
            <button onclick="addTool('breathing')">🧘 Breathe</button>
            <button onclick="addTool('journal')">📝 Journal</button>
          </div>
          <form class="input-area" onsubmit="sendMessage(event)">
            <textarea id="userInput" class="input-modern" placeholder="Type something you're feeling..." autocomplete="off" rows="1" oninput="autoExpand(this)"></textarea>
            <button type="submit">Send</button>
          </form>
        `;
        const chatContainer = document.getElementById('chat-container');
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
      
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
      

