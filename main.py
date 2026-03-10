from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import uuid
from pathlib import Path

from summarize_reviews import summarize_reviews, load_reviews_from_json

app = FastAPI()


class ScrapeRequest(BaseModel):
    url: str
    place_name: str | None = None


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Google Reviews Scraper API"}


@app.post("/scrape")
def scrape(request: ScrapeRequest):
    """
    Runs the Google Reviews scraper for a single URL
    and returns overall rating + top 10 reviews.
    """
    run_id = uuid.uuid4().hex
    json_path = Path(f"google_reviews_{run_id}.json")

    cmd = [
        "python",
        "start.py",
        "--url",
        request.url,
    ]

    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Scraper timed out")

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Scraper failed: {result.stderr[:500]}")

    if not json_path.exists():
        raise HTTPException(status_code=500, detail="Scraper did not produce JSON output")

    reviews = load_reviews_from_json(str(json_path))
    summary = summarize_reviews(reviews, place_name=request.place_name or "")

    try:
        json_path.unlink(missing_ok=True)
    except Exception:
        pass

    return summary
