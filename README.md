# password-reset-api

Password reset API built with Django REST Framework (group assignment).

This repository is split across feature branches:

- `main` — shared baseline
- `reset-request` — **POST /password-reset-request** (this branch)
- `reset-confirm` — POST /password-reset-confirm (partner's work)

## Features (reset-request branch)

`POST /password-reset-request`

- Accepts an `email` in the request body.
- If the email belongs to a registered user, a secure single-use token is
  generated, stored, and a reset email is **simulated** (printed to the console).
- Always returns a generic `200 OK` message — the response is identical whether
  or not the email exists, to prevent email enumeration.
- Rate limited to **5 requests per hour per IP**; further requests get `429`.

### Token model

`PasswordResetToken` stores the email, a cryptographically secure token,
`created_at`, and an `is_used` flag. Tokens expire **15 minutes** after creation
(`is_expired()` / `is_valid()`).

## Setup

```bash
python -m venv venv
source venv/Scripts/activate      # Windows (Git Bash)
# source venv/bin/activate        # macOS / Linux
pip install -r requirements.txt
cp .env.example .env              # then edit secrets
python manage.py migrate
python manage.py runserver
```

## Usage

```bash
curl -X POST http://127.0.0.1:8000/password-reset-request \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
```

Response (always, for any valid email format):

```json
{"message": "If an account with that email exists, a password reset link has been sent."}
```

When the rate limit is exceeded:

```json
{"message": "Too many password reset requests. Please wait before trying again.", "retry_after_seconds": 3600}
```

## Running tests

```bash
python manage.py test
```

## Environment variables

See `.env.example`. The real `.env` file is git-ignored.

| Variable        | Description                          |
| --------------- | ------------------------------------ |
| `SECRET_KEY`    | Django secret key                    |
| `DEBUG`         | `True` / `False`                     |
| `ALLOWED_HOSTS` | Comma-separated list of hosts        |
