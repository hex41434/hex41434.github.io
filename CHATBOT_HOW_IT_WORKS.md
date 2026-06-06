# How The Chatbot Works

The chatbot does not automatically read or crawl the whole website.

It answers from a prepared knowledge base file:

```text
hex41434.github.io/data/aida-chatbot-knowledge.json
```

## Flow

1. The user asks a question in the website chat UI.
2. `js/chatbot.js` sends the question to the backend:

   ```text
   http://127.0.0.1:8000/api/chat
   ```

3. The backend searches the knowledge base for the most relevant chunks.
4. The backend sends only those chunks plus the user question to the local Ollama model.
5. The model writes an answer using that supplied context.

## Important

If something is missing from `data/aida-chatbot-knowledge.json`, the chatbot may say that the website does not include that information, even if the information exists somewhere else.

To improve answers, update the knowledge base file with the facts the chatbot should know.

## Local Services

Local testing uses three pieces:

```text
Website:     http://127.0.0.1:8080/
Backend:     http://127.0.0.1:8000/api/chat
Ollama:      http://127.0.0.1:11434
```

Use:

```bash
cd /Users/a.farahani/Documents/MyRepos/aifa/personalwebpage
./start-chatbot-local.sh
```
