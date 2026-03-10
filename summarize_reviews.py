import json
from typing import Any, Dict, List


def summarize_reviews(reviews: List[Dict[str, Any]], place_name: str = "") -> Dict[str, Any]:
    if not reviews:
        return {
            "place_name": place_name,
            "overall_rating": None,
            "review_count": 0,
            "top_reviews": []
        }

    ratings = [r.get("rating", 0) for r in reviews if r.get("rating") is not None]
    overall_rating = sum(ratings) / len(ratings) if ratings else None

    sorted_reviews = sorted(
        reviews,
        key=lambda r: (r.get("rating", 0), r.get("likes", 0)),
        reverse=True
    )

    top10 = []
    for r in sorted_reviews[:10]:
        desc = r.get("description", {})
        text = desc.get("en") or (next(iter(desc.values()), "") if isinstance(desc, dict) and desc else "")
        top10.append({
            "rating": r.get("rating"),
            "text": text,
            "likes": r.get("likes", 0),
        })

    return {
        "place_name": place_name,
        "overall_rating": overall_rating,
        "review_count": len(reviews),
        "top_reviews": top10
    }


def load_reviews_from_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
