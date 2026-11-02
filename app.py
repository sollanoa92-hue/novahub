import os, time, requests
from collections import defaultdict, deque
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Main AI provider (set these in Render > Environment)
BASE_URL = os.getenv("AI_BASE_URL", "https://gen.pollinations.ai/v1/chat/completions")
API_KEY = os.getenv("AI_API_KEY", "")
MODEL = os.getenv("AI_MODEL", "openai")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1500"))
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MIN", "12"))
hits = defaultdict(deque)

# Providers are tried in order. The backup (AI2_*) is optional.
PROVIDERS = [(BASE_URL, API_KEY, MODEL)]
if os.getenv("AI2_BASE_URL"):
    PROVIDERS.append((os.getenv("AI2_BASE_URL"), os.getenv("AI2_API_KEY", ""), os.getenv("AI2_MODEL", "")))

DETAIL = " Give complete, well-structured, detailed answers."

PERSONAS = {
    "tutor":  {"name": "Study Tutor", "icon": "🎓", "tagline": "Learns with you, step by step",
               "prompt": "You are a patient tutor. Explain clearly with examples, then ask one short check-question."},
    "fixit":  {"name": "Fix-It Tech", "icon": "🛠️", "tagline": "Computer & phone troubleshooting",
               "prompt": "You are an IT support technician. Ask for symptoms if unclear, then give numbered, safe troubleshooting steps from easiest to hardest."},
    "coder":  {"name": "Code Buddy", "icon": "💻", "tagline": "Debug and write code",
               "prompt": "You are a senior developer. Give correct, clear code in fenced blocks and explain how it works."},
    "writer": {"name": "Word Smith", "icon": "✍️", "tagline": "Essays, emails, captions",
               "prompt": "You are a skilled writing assistant. Improve clarity and tone, and provide a full revised version."},
    "eli5":   {"name": "Explain Like I'm 5", "icon": "🧸", "tagline": "Hard ideas made simple",
               "prompt": "Explain everything in very simple words with a fun everyday analogy and a small example."},
}

def call_provider(url, key, model, messages):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    r = requests.post(url, headers=headers, timeout=35, json={
        "model": model, "messages": messages,
        "max_tokens": MAX_TOKENS, "temperature": 0.7})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

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

    full = [{"role": "system", "content": persona["prompt"] + DETAIL}] + msgs

    for i, (url, key, model) in enumerate(PROVIDERS):
        tries = 2 if i == 0 else 1   # retry the main AI once, then use the backup
        for attempt in range(tries):
            try:
                return jsonify(reply=call_provider(url, key, model, full))
            except Exception as e:
                print("AI ERROR:", url, repr(e), flush=True)
                if attempt < tries - 1:
                    time.sleep(1.5)

    return jsonify(error="The AI is very busy right now. Please try again in a moment."), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
