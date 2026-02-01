# LLM Integration (OpenRouter)

This project uses OpenRouter for LLM summaries. Follow these steps to enable it.

## 1) Add environment variables
Create/update .env with the following values:
- LLM_ENABLED=true
- OPENROUTER_API_KEY=your_key_here
- OPENROUTER_MODEL=openai/gpt-4o-mini
- OPENROUTER_TIMEOUT=30
- OPENROUTER_SITE_URL=https://your-domain-or-localhost
- OPENROUTER_APP_NAME=Interview Companion

## 2) Ensure dependencies
These are already in requirements.txt:
- python-dotenv
- requests

## 3) Start the app
Run the server as usual.

## 4) Generate a summary
Open an interview, end it, and click Generate Summary. The app calls OpenRouter’s chat completions endpoint and parses JSON into:
- Summary
- Recommendation
- Recommendation justification

## 5) Troubleshooting
- If you see 401/403: check OPENROUTER_API_KEY.
- If you see 402: add credits or change to a cheaper model.
- If parsing looks wrong: regenerate summary; the parser cleans common JSON formatting issues.

## 6) Change model
Update OPENROUTER_MODEL in .env to any OpenRouter-supported chat model.
