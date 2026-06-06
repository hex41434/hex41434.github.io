# Aida Farahani Personal Website

Static GitHub Pages website with a floating chatbot UI.

The website files live in this repository:

```text
hex41434.github.io/
```

The local chatbot backend lives next to this repository:

```text
../chatbot-backend/
```

## Local Development

Use the helper script from the parent `personalwebpage` directory. This starts both the static website and the real chatbot backend.

```bash
cd /Users/a.farahani/Documents/MyRepos/aifa/personalwebpage
./start-chatbot-local.sh
```

Then open:

```text
http://127.0.0.1:8080/
```

Keep that terminal open while testing. Stop both servers with `Ctrl + C`.

## What The Script Starts

The helper script starts:

```text
Website:         http://127.0.0.1:8080/
Chatbot API:     http://127.0.0.1:8000/api/chat
Ollama API:      http://127.0.0.1:11434
Default model:   qwen2.5:7b
```

The chatbot frontend in `js/chatbot.js` automatically uses `http://127.0.0.1:8000/api/chat` when the page is opened locally.

## Requirements

Before running the helper script, Ollama must be installed and running.

Check Ollama:

```bash
curl http://127.0.0.1:11434/api/tags
```

The default model is:

```text
qwen2.5:7b
```

If it is missing, pull it:

```bash
ollama pull qwen2.5:7b
```

## Test The Chatbot

After starting the local stack, test the backend directly:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What does Aida work on?"}'
```

A real response should look like:

```json
{
  "answer": "Aida Farahani works on ...",
  "sources": ["profile", "about", "expertise"]
}
```

Then test from the browser:

1. Open `http://127.0.0.1:8080/`.
2. Click `Ask Aida AI`.
3. Send a question.
4. Confirm the response is a real answer, not a mock response.

## Run Only The Static Website

If you only need to preview the page without the real chatbot backend:

```bash
cd /Users/a.farahani/Documents/MyRepos/aifa/personalwebpage/hex41434.github.io
python3 -m http.server 8080
```

Open:

```text
http://127.0.0.1:8080/
```

The page will load, but the chatbot will not answer unless the backend is also running on port `8000`.

## Troubleshooting

### `127.0.0.1 refused to connect`

If the browser shows:

```text
ERR_CONNECTION_REFUSED
```

for `http://127.0.0.1:8080/`, the website server is not running.

Fix:

```bash
cd /Users/a.farahani/Documents/MyRepos/aifa/personalwebpage
./start-chatbot-local.sh
```

Then reload `http://127.0.0.1:8080/`.

### Chatbot Says It Is Currently Unavailable

If the page loads but the chatbot says:

```text
The chatbot is currently unavailable. You can still contact Aida by email or use the CV and profile links on this page.
```

the website is running, but the chatbot API is not working at:

```text
http://127.0.0.1:8000/api/chat
```

Check whether anything is listening on port `8000`:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Then test the backend:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"hi"}'
```

If this fails, start the real local stack:

```bash
cd /Users/a.farahani/Documents/MyRepos/aifa/personalwebpage
./start-chatbot-local.sh
```

### Chatbot Returns `Mock chatbot response for: ...`

This means a temporary mock server is running on port `8000` instead of the real chatbot backend.

Stop the mock server with `Ctrl + C` in the terminal where it is running.

If you cannot find that terminal, identify the process:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Then stop it:

```bash
kill <PID>
```

Start the real stack again:

```bash
cd /Users/a.farahani/Documents/MyRepos/aifa/personalwebpage
./start-chatbot-local.sh
```

### Ollama Is Not Responding

If the backend starts but cannot generate answers, check Ollama:

```bash
curl http://127.0.0.1:11434/api/tags
```

If that fails, start Ollama and run the local stack again.

### Port Is Already In Use

If port `8080` or `8000` is already busy, find the process:

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Stop the old process if it is not needed:

```bash
kill <PID>
```

## Production Chatbot URL

For GitHub Pages production, configure the chatbot API before `js/chatbot.js` loads:

```html
<script>
  window.AIDA_CHATBOT_API_URL = "https://your-chatbot-api.example.com/api/chat";
</script>
```

The production endpoint must use HTTPS and return JSON with an `answer` field.
