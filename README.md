# NovaHub – Free multi-persona AI chat

## Run locally
    pip install -r requirements.txt
    python app.py        # open http://localhost:5000

## Deploy free (Render.com)
1. Push this folder to a GitHub repo.
2. Render → New → Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Deploy. Share the URL.

## Optional: use another free provider (env vars)
| Provider | AI_BASE_URL | AI_MODEL | AI_API_KEY |
|---|---|---|---|
| Pollinations (default, no key) | (leave empty) | (leave empty) | (leave empty) |
| Groq free tier | https://api.groq.com/openai/v1/chat/completions | llama-3.1-8b-instant | your key |
| OpenRouter free models | https://openrouter.ai/api/v1/chat/completions | a ":free" model | your key |

Add personas by editing the PERSONAS dict in app.py.
