from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from shortener import generate_unique_short_code
from database import create_url, init_db, get_original_url, increment_click_count

class URLRequest(BaseModel):
    url: HttpUrl

app = FastAPI()

@app.get("/")
def read_root():
    return {"status" : "ok"}

init_db()

@app.post("/shorten")
def shorten_url(payload: URLRequest, request: Request):
    short_code = generate_unique_short_code()
    create_url(short_code, str(payload.url))
    return {"short_code": short_code, "short_url": f"{request.base_url}{short_code}"}

@app.get("/{short_code}")
def redirect_to_url(short_code: str):
    original_url = get_original_url(short_code)
    if original_url is None:
        raise HTTPException(status_code=404, detail="Short code not found")
    increment_click_count(short_code)
    return RedirectResponse(url=original_url, status_code=302)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")
