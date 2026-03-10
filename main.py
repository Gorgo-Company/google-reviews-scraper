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
    db_path = Path(f"reviews_{run_id}.db")
    json_path = Path(f"google_reviews_{run_id}.json")

    # 1) Scrape into a temporary SQLite DB
    scrape_cmd = [
        "python",
        "start.py",
        "scrape",
        "--url",
        request.url,
        "--db-path",
        str(db_path),
    ]

    try:
        scrape_result = subprocess.run(
            scrape_cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=240,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Scraper timed out during scrape")

    if scrape_result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Scrape failed: {scrape_result.stderr[:500]}")

    # 2) Export all reviews from that DB to JSON
    export_cmd = [
        "python",
        "start.py",
        "export",
        "--db-path",
        str(db_path),
        "--format",
        "json",
        "--output",
        str(json_path),
    ]

    try:
        export_result = subprocess.run(
            export_cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=240,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Scraper timed out during export")

    if export_result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Export failed: {export_result.stderr[:500]}")

    if not json_path.exists():
        raise HTTPException(status_code=500, detail="Export did not produce JSON output")

    reviews = load_reviews_from_json(str(json_path))
    summary = summarize_reviews(reviews, place_name=request.place_name or "")

    # cleanup
    try:
        json_path.unlink(missing_ok=True)
        db_path.unlink(missing_ok=True)
    except Exception:
        pass

    return summary

