/**
 * script.js
 * Owner: Member 1 - Frontend Developer
 *
 * Talks to the backend API (Member 2's FastAPI app) for:
 *   - Conversational chat: POST /api/chat
 *   - Direct scheme search: POST /api/schemes/search
 *
 * Update API_BASE_URL to point at wherever the backend is deployed/running.
 */

const API_BASE_URL = "http://localhost:8000";

let sessionId = null;       // returned by the backend after the first message, then reused
let currentLanguage = "en"; // "en" | "te" — purely a UI hint; the backend auto-detects language too

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const profileSummary = document.getElementById("profile-summary");
const welcomeMessage = document.getElementById("welcome-message");

const searchInput = document.getElementById("scheme-search-input");
const searchBtn = document.getElementById("scheme-search-btn");
const searchResults = document.getElementById("search-results");

const langButtons = document.querySelectorAll(".lang-btn");

const UI_TEXT = {
  en: {
    welcome: "Hello! Tell me a bit about yourself — your age, occupation, and state — and I'll help you find government schemes you may be eligible for.",
    placeholder: "e.g. I am a 62 year old farmer in Andhra Pradesh...",
    send: "Send",
    thinking: "Thinking...",
  },
  te: {
    welcome: "నమస్కారం! మీ వయస్సు, వృత్తి, రాష్ట్రం గురించి కొంచెం చెప్పండి — మీకు అర్హత ఉన్న ప్రభుత్వ పథకాలను కనుగొనడంలో సహాయం చేస్తాను.",
    placeholder: "ఉదా. నేను 62 ఏళ్ల రైతును, ఆంధ్రప్రదేశ్ లో ఉంటాను...",
    send: "పంపు",
    thinking: "ఆలోచిస్తున్నాను...",
  },
};

// ---------- Language toggle ----------
langButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    langButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentLanguage = btn.dataset.lang;
    applyLanguageUI();
  });
});

function applyLanguageUI() {
  const t = UI_TEXT[currentLanguage];
  welcomeMessage.textContent = t.welcome;
  chatInput.placeholder = t.placeholder;
  sendBtn.textContent = t.send;
}

// ---------- Chat ----------
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendMessage(message, "user");
  chatInput.value = "";
  setSending(true);

  const typingEl = appendTypingIndicator();

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);

    const data = await response.json();
    sessionId = data.session_id;

    typingEl.remove();
    appendMessage(data.reply, "assistant");
    updateProfileSummary(data.profile);
  } catch (err) {
    typingEl.remove();
    appendMessage(
      "Sorry, something went wrong reaching the assistant. Please check that the backend server is running and try again.",
      "assistant"
    );
    console.error(err);
  } finally {
    setSending(false);
  }
});

function appendMessage(text, role) {
  const el = document.createElement("div");
  el.className = `message ${role}-message`;
  const p = document.createElement("p");
  p.textContent = text;
  el.appendChild(p);
  chatWindow.appendChild(el);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function appendTypingIndicator() {
  const el = document.createElement("div");
  el.className = "typing-indicator";
  el.textContent = UI_TEXT[currentLanguage].thinking;
  chatWindow.appendChild(el);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return el;
}

function setSending(isSending) {
  sendBtn.disabled = isSending;
  chatInput.disabled = isSending;
}

function updateProfileSummary(profile) {
  const parts = [];
  if (profile.age) parts.push(`Age: ${profile.age}`);
  if (profile.occupation) parts.push(`Occupation: ${profile.occupation}`);
  if (profile.state) parts.push(`State: ${profile.state}`);
  if (profile.education) parts.push(`Education: ${profile.education}`);
  if (profile.income) parts.push(`Income: ${profile.income}`);

  if (parts.length === 0) {
    profileSummary.classList.add("hidden");
    return;
  }
  profileSummary.textContent = "Profile so far — " + parts.join(" · ");
  profileSummary.classList.remove("hidden");
}

// ---------- Direct scheme search ----------
searchBtn.addEventListener("click", performSearch);
searchInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") performSearch();
});

async function performSearch() {
  const query = searchInput.value.trim();
  if (!query) return;

  searchResults.innerHTML = "<p>Searching...</p>";
  searchResults.classList.remove("hidden");

  try {
    const response = await fetch(`${API_BASE_URL}/api/schemes/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: 5 }),
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);

    const data = await response.json();
    renderSearchResults(data.results);
  } catch (err) {
    searchResults.innerHTML = "<p>Could not fetch search results. Is the backend running?</p>";
    console.error(err);
  }
}

function renderSearchResults(results) {
  if (!results || results.length === 0) {
    searchResults.innerHTML = "<p>No matching schemes found.</p>";
    return;
  }

  searchResults.innerHTML = "";
  results.forEach(({ scheme }) => {
    const card = document.createElement("div");
    card.className = "scheme-card";
    card.innerHTML = `
      <h4>${scheme.name_en}</h4>
      <div class="meta">${scheme.level} · ${scheme.state} · ${scheme.category}</div>
      <p>${scheme.benefits}</p>
      <a href="${scheme.official_source}" target="_blank" rel="noopener">Official source ↗</a>
    `;
    searchResults.appendChild(card);
  });
}

// ---------- Init ----------
applyLanguageUI();
