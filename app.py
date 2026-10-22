import os, time, requests
from collections import defaultdict, deque
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Free by default (no key needed). Swap provider with env vars, e.g. Groq / OpenRouter free tiers.
BASE_URL = os.getenv("AI_BASE_URL", "https://text.pollinations.ai/openai")
API_KEY = os.getenv("AI_API_KEY", "")
MODEL = os.getenv("AI_MODEL", "openai")
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MIN", "12"))
hits = defaultdict(deque)

PERSONAS = {
    "tutor":  {"name": "Study Tutor", "icon": "🎓", "tagline": "Learns with you, step by step",
               "prompt": "You are a patient tutor. Explain simply, use examples, then ask one short check-question."},
    "fixit":  {"name": "Fix-It Tech", "icon": "🛠️", "tagline": "Computer & phone troubleshooting",
               "prompt": "You are an IT support technician. Ask for symptoms if unclear, then give numbered, safe troubleshooting steps from easiest to hardest."},
    "coder":  {"name": "Code Buddy", "icon": "💻", "tagline": "Debug and write code",
               "prompt": "You are a senior developer. Give correct, concise code in fenced blocks with a brief explanation."},
    "writer": {"name": "Word Smith", "icon": "✍️", "tagline": "Essays, emails, captions",
               "prompt": "You are a skilled writing assistant. Improve clarity and tone, and offer a short revised version."},
    "eli5":   {"name": "Explain Like I'm 5", "icon": "🧸", "tagline": "Hard ideas made simple",
               "prompt": "Explain everything in very simple words with a fun everyday analogy. Keep it short."},
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/personas")
def personas():
    return jsonify({k: {x: v[x] for x in ("name", "icon", "tagline")} for k, v in PERSONAS.items()})

@app.route("/api/chat", methods=["POST"])
def chat():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0].strip()
    now, q = time.time(), hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return jsonify(error="Too many messages. Please wait a minute."), 429
    q.append(now)

    data = request.get_json(silent=True) or {}
    persona = PERSONAS.get(data.get("persona"), PERSONAS["tutor"])
    msgs = [{"role": m["role"], "content": str(m["content"])[:2000]}
            for m in data.get("messages", [])[-20:]
            if isinstance(m, dict) and m.get("role") in ("user", "assistant")]
    if not msgs:
        return jsonify(error="Empty message."), 400

    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    try:
        r = requests.post(BASE_URL, headers=headers, timeout=60, json={
            "model": MODEL,
            "messages": [{"role": "system", "content": persona["prompt"]}] + msgs})
        r.raise_for_status()
        reply = r.json()["choices"][0]["message"]["content"]
        return jsonify(reply=reply)
    except Exception:
        return jsonify(error="The AI service is busy right now. Try again shortly."), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
