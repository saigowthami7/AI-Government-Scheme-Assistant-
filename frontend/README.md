# Member 1 – Frontend Developer

## Your responsibilities (from the project proposal)
- UI
- Chatbot interface
- Scheme search
- Telugu/English interface

## What's in this package

| File | Purpose |
|---|---|
| `index.html` | Page structure: header with language toggle, a direct scheme-search bar, and the conversational chat window. |
| `style.css` | All styling — clean, government-portal-appropriate look (green/amber palette), mobile responsive. |
| `script.js` | All frontend logic: calls the backend `/api/chat` and `/api/schemes/search` endpoints, renders messages and scheme cards, handles the English/Telugu toggle. |

## Setup

No build tools needed — this is plain HTML/CSS/JS so it's easy to open directly or serve statically.

```bash
cd frontend
python -m http.server 3000
# then open http://localhost:3000
```

**Before running:** make sure Member 2's backend server is running (default `http://localhost:8000`) — see `backend/README.md`. If you change the backend port/host, update `API_BASE_URL` at the top of `script.js`.

## How it talks to the backend (API contract from Member 2)

- `POST /api/chat` — send `{ session_id, message }`, get back `{ session_id, reply, language, profile, matched_schemes }`. The frontend stores `session_id` in a JS variable after the first response and reuses it for every follow-up message so the conversation and extracted profile (age/state/occupation/etc.) persist.
- `POST /api/schemes/search` — send `{ query, top_k }`, get back a list of `{ scheme, relevance_score }` for the standalone search bar (outside the chat flow).

Full request/response shapes are documented in `backend/README.md` and live at `http://localhost:8000/docs` once the backend is running.

## Language toggle

The two buttons (`English` / `తెలుగు`) only change the **UI chrome text** (placeholders, button labels, welcome message) — the actual chatbot reply language is auto-detected by the backend based on what language the user types their message in (see `llm_nlp/multilingual.py`). Users can type in Telugu even with the English button selected and still get a Telugu reply.

## Notes for review / demo

- Currently a single static page for simplicity — a natural next step is breaking `script.js` into components (e.g. React) if the team wants richer UI (loading skeletons, eligibility badges from `matched_schemes`, etc.).
- `matched_schemes` (returned by `/api/chat`) includes a `match_signal` per scheme (`likely_match`/`possible_match`/etc.) from Member 4's eligibility matcher — not yet rendered in the UI. Good next feature: show this as a colored badge next to each scheme mentioned in the chat.
- No authentication/login is implemented — sessions are anonymous and tied only to the browser's in-memory `sessionId` variable (lost on page refresh). Add persistence (e.g. localStorage) if "resume my chat" is needed.
