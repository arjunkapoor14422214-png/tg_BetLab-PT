# BetLab Portugal Telegram Bot

Telegram bot for reposting source channel posts into a target channel with AI rewriting to Portuguese, bookmaker replacement rules, promo normalization, and media forwarding.

## Files

- `main.py` - main worker
- `render.yaml` - Render worker configuration
- `.env.example` - required environment variables
- `export_session.py` - helper to export a Telethon session string

## Render

1. Create a new Worker service from this repository.
2. Render will detect `render.yaml`.
3. Set the required environment variables from `.env.example`.
4. Start the worker.

## Important

- Do not commit `.env` or `.session` files.
- The Telegram account behind `TG_SESSION_STRING` must have access to every source channel.
- For live AI rewriting, set `AI_API_KEY` or `OPENAI_API_KEY`.
