# Local Chatbot Testing

Use this guide to run the GitHub Pages site locally and test the chatbot UI.

## 1. Start the local website

From the repository root:

```bash
cd /Users/a.farahani/Documents/MyRepos/aifa/personalwebpage/hex41434.github.io
python3 -m http.server 8080
```

Open the site in a browser:

```text
http://127.0.0.1:8080/
```

Keep the terminal window open while testing. Stop the website server with `Ctrl + C`.

If port `8080` is already in use, use another port:

```bash
python3 -m http.server 8081
```

Then open:

```text
http://127.0.0.1:8081/
```

## 2. Start a local chatbot API

When the site runs locally, `js/chatbot.js` sends chatbot requests to:

```text
http://127.0.0.1:8000/api/chat
```

The API must accept a `POST` request with this body:

```json
{
  "message": "What does Aida work on?"
}
```

It must return JSON with an `answer` field:

```json
{
  "answer": "Aida works on industrial AI, computer vision, data-centric AI, and deployed machine learning workflows."
}
```

## 3. Quick mock backend for UI testing

If the real chatbot backend is not running yet, use this temporary Python mock server in a separate terminal:

```bash
python3 - <<'PY'
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class ChatHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            data = json.loads(body or b"{}")
        except json.JSONDecodeError:
            data = {}

        question = data.get("message", "")
        response = {
            "answer": f"Mock chatbot response for: {question}"
        }

        payload = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

HTTPServer(("127.0.0.1", 8000), ChatHandler).serve_forever()
PY
```

Then open `http://127.0.0.1:8080/`, click the chatbot launcher, send a question, and confirm that the mock response appears.

Stop the mock backend with `Ctrl + C`.

## 4. Expected local behavior

- If the website server is not running, the browser shows `ERR_CONNECTION_REFUSED`.
- If the website is running but the chatbot API is not running, the page loads but the chatbot shows an unavailable message after you send a question.
- If both servers are running, the chatbot should display the API response in the chat panel.
