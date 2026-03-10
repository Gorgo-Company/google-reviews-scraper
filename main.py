from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
from pathlib import Path
import uuid

app = FastAPI()


class ScrapeRequest(BaseModel):
    url: str
    place_name: str | None = None


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Google Reviews Scraper API placeholder"}


@app.post("/scrape")
def scrape(request: ScrapeRequest):
    """
    Temporary implementation:
    - Runs the CLI scraper with the given URL.
    - Returns the CLI stdout/stderr so we can see exactly what the tool is doing.
    - Does NOT yet parse reviews; that part is disabled until the export path is stable.
    """
    run_id = uuid.uuid4().hex
    db_path = Path(f"reviews_{run_id}.db")

    # Call the scraper in "scrape" mode, writing into a temp DB
    cmd = [
        "python",
        "start.py",
        "scrape",
        "--url",
        request.url,
        "--db-path",
        str(db_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Scraper timed out")

    # Clean up DB if it exists (we're not using it yet)
    try:
        if db_path.exists():
            db_path.unlink()
    except Exception:
        pass

    if result.returncode != 0:
        # Return stderr/stdout so you can see the real error in Make
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Scraper CLI failed",
                "returncode": result.returncode,
                "stdout": result.stdout[-1000:],
                "stderr": result.stderr[-1000:],
            },
        )

    # Placeholder summary until export/parsing is wired correctly
    return {
        "place_name": request.place_name or "",
        "overall_rating": None,
        "review_count": None,
        "top_reviews": [],
        "raw_stdout": result.stdout[-1000:],
        "note": "Scrape succeeded at CLI level; JSON export/parsing not yet wired.",
    }
