// ===== ELEMENTS =====
const chatArea = document.getElementById('chatArea');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');
const attachBtn = document.getElementById('attachBtn');
const fileInput = document.getElementById('fileInput');
const newChatBtn = document.getElementById('newChatBtn');
const historyList = document.getElementById('historyList');
const exportBtn = document.getElementById('exportBtn');
const themeToggle = document.getElementById('themeToggle');
const menuIcon = document.getElementById('menuIcon');
const sidebar = document.getElementById('sidebar');
const langSelect = document.getElementById('langSelect');

// ===== BACKEND URL =====
const API_URL = '';

let chatHistory = [];

// ===== LANGUAGE MAP =====
const langMap = {
    'en': 'en-US',
    'hi': 'hi-IN',
    'kn': 'kn-IN',
    'ta': 'ta-IN',
    'te': 'te-IN',
    'mr': 'mr-IN',
    'fr': 'fr-FR',
    'es': 'es-ES',
    'de': 'de-DE',
    'ja': 'ja-JP',
    'zh': 'zh-CN',
    'ar': 'ar-SA'
};

// ===== SPEAK TEXT (TEXT TO SPEECH) =====
function speakText(text) {
    window.speechSynthesis.cancel();

    function doSpeak() {
        var utterance = new SpeechSynthesisUtterance(text);
        var selectedLang = langSelect ? langSelect.value : 'en';
        var fullLang = langMap[selectedLang] || 'en-US';

        utterance.lang = fullLang;
        utterance.rate = 0.95;
        utterance.pitch = 1;
        utterance.volume = 1;

        var voices = window.speechSynthesis.getVoices();
        var matchedVoice = null;

        for (var i = 0; i < voices.length; i++) {
            if (voices[i].lang === fullLang) {
                matchedVoice = voices[i];
                break;
            }
        }

        if (!matchedVoice) {
            var prefix = fullLang.split('-')[0];
            for (var j = 0; j < voices.length; j++) {
                if (voices[j].lang.startsWith(prefix)) {
                    matchedVoice = voices[j];
                    break;
                }
            }
        }

        if (matchedVoice) {
            utterance.voice = matchedVoice;
        }

        window.speechSynthesis.speak(utterance);
    }

    var voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
        doSpeak();
    } else {
        window.speechSynthesis.onvoiceschanged = function () {
            doSpeak();
        };
    }
}

// ===== ADD MESSAGE =====
function addMessage(sender, text) {
    const msg = document.createElement('div');
    msg.className = 'message ' + sender;
    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = sender === 'user' ? 'YOU' : 'ARIA';
    const body = document.createElement('div');
    body.className = 'message-text';
    body.textContent = text;
    msg.appendChild(label);
    msg.appendChild(body);
    chatArea.appendChild(msg);
    chatArea.scrollTop = chatArea.scrollHeight;
    chatHistory.push({ sender, text });

    // Speak AI replies automatically
    if (sender === 'aria') {
        speakText(text);
    }
}

// ===== ADD HISTORY ITEM =====
function addHistory(text) {
    const item = document.createElement('div');
    item.className = 'history-item';
    item.textContent = text.length > 25 ? text.substring(0, 25) + '...' : text;
    item.onclick = () => alert('Load chat: ' + text);
    historyList.appendChild(item);
}

// ===== SEND MESSAGE =====
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    window.speechSynthesis.cancel();
    addMessage('user', text);

    if (chatHistory.filter(m => m.sender === 'user').length === 1) {
        addHistory(text);
    }

    chatInput.value = '';

    try {
        const response = await fetch(API_URL + '/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                language: langSelect.value
            })
        });

        if (!response.ok) throw new Error('Server error');

        const data = await response.json();
        addMessage('aria', data.reply || data.response || 'No response received');
    } catch (err) {
        addMessage('aria', 'Could not reach server. Make sure it is running.');
    }
}

// ===== VOICE INPUT =====
let recognition = null;
let isListening = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        sendMessage();
    };

    recognition.onend = () => {
        isListening = false;
        micBtn.classList.remove('active');
    };

    recognition.onerror = () => {
        isListening = false;
        micBtn.classList.remove('active');
    };
}

micBtn.addEventListener('click', () => {
    if (!recognition) {
        alert('Speech recognition not supported. Use Chrome browser.');
        return;
    }

    window.speechSynthesis.cancel();

    if (isListening) {
        recognition.stop();
    } else {
        recognition.lang = langMap[langSelect.value] || 'en-US';
        recognition.start();
        isListening = true;
        micBtn.classList.add('active');
    }
});

// ===== FILE ATTACH =====
attachBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    addMessage('user', 'Uploaded: ' + file.name);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(API_URL + '/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        addMessage('aria', data.message || data.reply || 'File received successfully.');
    } catch {
        addMessage('aria', 'File upload failed. Backend not reachable.');
    }
});

// ===== NEW CHAT =====
newChatBtn.addEventListener('click', () => {
    window.speechSynthesis.cancel();
    chatArea.innerHTML = '';
    chatHistory = [];
});

// ===== EXPORT CHAT =====
exportBtn.addEventListener('click', () => {
    if (chatHistory.length === 0) {
        alert('No chat to export!');
        return;
    }
    const text = chatHistory.map(m =>
        m.sender.toUpperCase() + ': ' + m.text
    ).join('\n\n');

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'aria-chat-' + Date.now() + '.txt';
    a.click();
    URL.revokeObjectURL(url);
});

// ===== THEME TOGGLE =====
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('light');
    themeToggle.textContent = document.body.classList.contains('light')
        ? 'Dark Mode' : 'Light Mode';
});

// ===== SIDEBAR TOGGLE =====
menuIcon.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
});

// ===== ENTER KEY =====
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// ===== SEND BUTTON =====
sendBtn.addEventListener('click', sendMessage);