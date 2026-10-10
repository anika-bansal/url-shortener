**Live demo:** https://url-shortener-huie.onrender.com/static/

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
pip install -r requirements.txt
uvicorn main:app --reload
```
Then open `http://127.0.0.1:8000/static/`.

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

## Schema

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Auto-incrementing primary key |
| short_code | TEXT | Unique, indexed via the UNIQUE constraint |
| original_url | TEXT | The destination URL |
| created_at | TEXT | UTC timestamp, ISO format |
| click_count | INTEGER | Defaults to 0; incremented atomically on each redirect |

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

- **Data does not persist across cold starts.** The app runs on Render's
  free tier, which spins down after 15 minutes of inactivity and restarts
  on the next request. Because the SQLite database lives on the instance's
  disk (not a persistent volume), a restart starts with an empty database —
  any short link created in an earlier session will 404 if visited after
  a restart. Links created and followed within the same session are
  unaffected, since both actions hit the same running instance. This is a
  known trade-off of free-tier hosting; a production version would move
  the database to a managed service like Postgres, kept separate from the
  app's own ephemeral compute.
- Cold start from a spun-down instance measured at ~24s; a warm request
  returns in ~0.5s.
- `datetime.utcnow()` is deprecated in newer Python versions in favor of
  timezone-aware objects; noted by pytest but not yet addressed.
- No URL normalization — `https://example.com` and `https://example.com/`
  are treated as distinct URLs.
- Frontend error messages trim Pydantic's validation text by splitting on
  the first comma — a pragmatic fix, not a fully robust one.
- No rate limiting. `/shorten` and the redirect endpoint both accept
  unlimited requests from any client — there's nothing stopping repeated
  automated requests from filling the database with junk entries or
  inflating click_count. A production version would add per-IP rate
  limiting (e.g. via `slowapi` or a reverse-proxy layer).

## Lessons learned

The first deployed version hardcoded `http://127.0.0.1:8000` into every
generated short URL — it worked perfectly in local testing (since that's
 the local address) but produced dead links the moment it was
deployed, since the public address is different. The existing test suite
didn't catch this because it only checked that a `short_url` field was
present, not that it pointed anywhere real. Fixed by building the URL from
the incoming request's actual host (`request.base_url`) instead of a fixed
string, and added a regression test asserting `127.0.0.1` never appears in
a generated short URL.
