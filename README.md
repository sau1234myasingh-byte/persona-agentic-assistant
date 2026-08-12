# Persona — AI Productivity Assistant

A Streamlit prototype for organising reminders and chatting with an AI assistant. It uses the Groq API for streamed LLM responses and includes a small, local nickname-to-email lookup.

> Built during my internship at **Cipher Web Academy**. This repository is shared as a learning and portfolio project. The original internship brief, starter material, and any academy guidance remain credited to Cipher Web Academy; the code and presentation should not be represented as entirely independently commissioned production work.

## What it does

- Tracks a demo unread-email count.
- Separates reminders into **Missed** and **Future** groups.
- Lets the user trash or reschedule a reminder during the current browser session.
- Resolves a few demo nicknames to placeholder email addresses.
- Streams a Groq-hosted LLM response when no nickname matches.

## Important prototype limitations

- The email counter is demo data; it does not connect to Gmail or any inbox.
- Reminders live only in Streamlit session state and disappear when the session resets.
- The nickname map is a small in-code demo mapping, not a database or vector store.
- The app sends chat prompts to Groq when the LLM feature is enabled. Do not submit confidential information.

## Tech stack

- Python
- Streamlit
- Groq Python SDK
- python-dotenv

## Project structure

```text
persona/
├── app.py              # Streamlit interface and session-state interactions
├── config.py           # App settings, demo memory map, API-key resolution
├── groq_client.py      # Streaming Groq client with retry/fallback support
├── logic.py            # Testable reminder and nickname logic
├── tests/              # Unit tests for the core logic
├── .env.example        # Safe environment-variable template
└── requirements.txt
```

## Run locally

1. Clone this repository and enter its directory.
2. Create and activate a virtual environment.

   ```bash
   python -m venv .venv
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   # macOS/Linux
   source .venv/bin/activate
   ```

3. Install the dependencies.

   ```bash
   pip install -r requirements.txt
   ```

4. Create a local environment file and add your Groq key.

   ```bash
   copy .env.example .env   # Windows
   # cp .env.example .env   # macOS/Linux
   ```

   Set `GROQ_API_KEY` in `.env`. Never commit this file.

5. Start the app.

   ```bash
   streamlit run app.py
   ```

## Run tests

From the project root:

```bash
python -m unittest discover -s tests -v
```

## Suggested next improvements

- Persist reminders in SQLite or another database.
- Add a form to create new reminders.
- Replace demo data with user-authorised calendar/email integrations.
- Add more tests and continuous integration.

## Publishing note

Before publishing, confirm that your internship agreement permits public sharing. This repository intentionally excludes API keys, local environment files, virtual environments, and generated caches. Avoid committing your internship certificate to the repository; share it separately only if you are comfortable with the personal details it contains.
