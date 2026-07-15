# Aida Website Chatbot Backend

FastAPI backend for the personal website chatbot. It exposes a narrow `POST /api/chat` endpoint, retrieves relevant facts from the static knowledge file, and calls a local Ollama server.

## Local Development

The easiest local path is to start both the backend and the static website from the `personalwebpage` directory:

```bash
./start-chatbot-local.sh
```

Then open:

```text
http://127.0.0.1:8080
```

Do not open `index.html` directly from Finder or the editor. The chatbot frontend expects the page to be served over HTTP so it can call the local API at `http://127.0.0.1:8000/api/chat`.

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install Ollama and pull the default model:

```bash
ollama pull qwen2.5:7b
```

If you already have another Ollama model, set it explicitly before starting the backend:

```bash
OLLAMA_MODEL=llama3.2:1b ./start-chatbot-local.sh
```

Run the backend:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Test it:

```bash
curl -s http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What computer vision projects has Aida worked on?"}'
```

## Environment Variables

- `OLLAMA_BASE_URL`: Ollama base URL. Default: `http://127.0.0.1:11434`.
- `OLLAMA_MODEL`: model name. Default: `qwen2.5:7b`.
- `ALLOWED_ORIGINS`: comma-separated browser origins allowed by CORS. Default includes local development and `https://hex41434.github.io`.
- `RATE_LIMIT_PER_MINUTE`: per-IP request limit. Default: `12`.
- `REQUEST_TIMEOUT_SECONDS`: Ollama request timeout. Default: `45`.
- `KNOWLEDGE_PATH`: optional path to `aida-chatbot-knowledge.json`.

## Docker

The included Docker Compose file mounts the static site's `data` directory read-only and calls Ollama on the host:

```bash
docker compose up --build -d
```

If Ollama runs in another container or on another host, update `OLLAMA_BASE_URL`.

## VPS Deployment

1. Provision a small EU VPS with at least 4 GB RAM; 8 GB is preferred.
2. Install Docker and Docker Compose.
3. Install or run Ollama.
4. Pull the default model:

   ```bash
   ollama pull qwen2.5:7b
   ```

5. Run this backend with Docker Compose or systemd.
6. Put Caddy or Nginx in front of the backend with HTTPS.
7. Expose only:
   - `443` for HTTPS
   - optionally `80` for certificate redirect
8. Keep Ollama bound to localhost. Do not expose port `11434` publicly.
9. Configure the static website before `js/chatbot.js` loads:

   ```html
   <script>
     window.AIDA_CHATBOT_API_URL = "https://chat.example.com/api/chat";
   </script>
   ```

## Caddy Example

```caddyfile
chat.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

## API

Request:

```json
{
  "message": "What projects has Aida worked on?"
}
```

Response:

```json
{
  "answer": "Aida has worked on ...",
  "sources": ["projects", "cv"]
}
```

## Guardrails

The backend prompt restricts answers to Aida Farahani's public profile, CV, projects, research, skills, education, contact, and website content. If a fact is not present in the supplied context, the model is instructed to say that the website does not include that information.
