# URL Shortener

A minimal full-stack URL shortener. Built to demonstrate backend
fundamentals: a non-ML Python backend, a real database, and the
API design decisions that come with building a redirect service.

## Stack

- Backend: FastAPI (Python)
- Database: SQLite
- Frontend: Plain HTML/CSS/JS (no framework)
- Deployment: Render

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn
uvicorn main:app --reload
```
Then open `http://127.0.0.1:8000/static/`.

## Schema

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Auto-incrementing primary key |
| short_code | TEXT | Unique, indexed via the UNIQUE constraint |
| original_url | TEXT | The destination URL |
| created_at | TEXT | UTC timestamp, ISO format |
| click_count | INTEGER | Defaults to 0; not yet incremented (see Limitations) |

## Design decisions

**Short codes are randomly generated (base62), not sequential.** A
sequential counter would make codes enumerable and guessable, letting
anyone scrape every link ever created just by incrementing a number.
Random generation is checked against the database for collisions before
being accepted, with the check confirmed via a forced-collision test.

**Redirects use HTTP 302, not 301.** A 301 (permanent redirect) gets
cached by the browser, meaning repeat visits may never reach the server
again — which would silently undercount clicks. 302 guarantees every
visit hits the server, keeping click_count accurate.

**Duplicate URLs create separate short codes.** Submitting the same URL
twice produces two independent codes rather than reusing one. This is
intentional: click_count is tracked per short code, so collapsing
duplicates would make it impossible to measure clicks from different
distribution channels (e.g. an email link vs. a social post) pointing at
the same destination.

## Known limitations

- No URL normalization — `https://example.com` and `https://example.com/`
  are treated as distinct URLs, which ties into the duplicate-handling
  decision above.
- Frontend error messages trim Pydantic's validation text by splitting on
  the first comma, which is a pragmatic fix rather than a fully robust
  one — a future version would write a custom validator instead.
- SQLite on Render's free tier may not persist across restarts (ephemeral
  filesystem); noted here ahead of deployment.
