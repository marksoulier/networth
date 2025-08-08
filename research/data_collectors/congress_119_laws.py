import os
from typing import List, Optional

import requests


API_KEY = os.environ.get("CONGRESS_API_KEY", "6uD30SiXqMt8DDtfY2hbX2EB5zofuveD7wfqIref")
CONGRESS = 119


def list_119th_congress_laws(api_key: str = API_KEY, limit: int = 1000) -> List[dict]:
    """Return the raw law listings for the 119th Congress.

    Note: The API may return data under keys like 'laws' or 'bills'. We normalize by
    checking both and returning whichever exists.
    """
    law_endpoint = f"https://api.congress.gov/v3/law/{CONGRESS}"
    resp = requests.get(law_endpoint, params={"api_key": api_key, "limit": limit}, timeout=60)
    resp.raise_for_status()
    data = resp.json() or {}
    items = data.get("laws") or data.get("bills") or []
    if not isinstance(items, list):
        return []
    return items


def fetch_full_law_text(text_content_url: str, *, timeout: int = 60) -> Optional[str]:
    """Fetch the full law text from a given 'Formatted Text' URL returned by the API."""
    if not text_content_url:
        return None
    r = requests.get(text_content_url, timeout=timeout)
    if r.status_code != 200:
        return None
    return r.text


def get_item_title(law_item: dict) -> Optional[str]:
    """Return title from a listing item when present (may be None)."""
    title = law_item.get("title")
    return str(title) if title else None


def fetch_bill_summary(bill_type: str, bill_num: str, *, api_key: str = API_KEY) -> Optional[str]:
    """Fetch a short summary for a bill/law using the summaries endpoint.

    Returns the first available summary text when present.
    """
    if not bill_type or not bill_num:
        return None
    url = f"https://api.congress.gov/v3/bill/{CONGRESS}/{bill_type}/{bill_num}/summaries"
    r = requests.get(url, params={"api_key": api_key}, timeout=60)
    if r.status_code != 200:
        return None
    summaries = r.json().get("summaries", [])
    if not summaries:
        return None
    text = summaries[0].get("text")
    return text if isinstance(text, str) and text.strip() else None


def process_law_item(item_index: int, law_item: dict, *, api_key: str = API_KEY) -> Optional[str]:
    """Process a single law listing: locate its formatted text URL and return the full text.

    Prints brief status lines and returns the full text when available.
    """
    bill_type = (law_item.get("type") or "").lower()
    bill_num = law_item.get("number")

    if not bill_type or not bill_num:
        print(f"{item_index}. Skipping item without bill identifiers")
        return None

    text_versions_url = f"https://api.congress.gov/v3/bill/{CONGRESS}/{bill_type}/{bill_num}/text"
    tv_resp = requests.get(text_versions_url, params={"api_key": api_key}, timeout=60)
    if tv_resp.status_code != 200:
        print(f"{item_index}. Failed to fetch text versions for {bill_type}-{bill_num}")
        return None

    text_versions = tv_resp.json().get("textVersions", [])
    if not text_versions:
        print(f"{item_index}. No text versions for {bill_type}-{bill_num}")
        return None

    chosen = next((v for v in text_versions if v.get("type") == "Enrolled Bill"), text_versions[0])
    formatted_url = None
    for fmt in chosen.get("formats", []):
        if fmt.get("type") == "Formatted Text" and fmt.get("url"):
            formatted_url = fmt["url"]
            break

    if not formatted_url:
        print(f"{item_index}. No 'Formatted Text' URL for {bill_type}-{bill_num}")
        return None

    full_text = fetch_full_law_text(formatted_url)
    if full_text:
        print(f"{item_index}. {bill_type}-{bill_num} full text length: {len(full_text):,}")
        return full_text

    print(f"{item_index}. Failed to fetch full text for {bill_type}-{bill_num}")
    return None


if __name__ == "__main__":
    print(f"=== Listing laws from {CONGRESS}th Congress ===")
    laws = list_119th_congress_laws()
    print(f"Found {len(laws)} items\n")

    for i, itm in enumerate(laws, 1):
        process_law_item(i, itm, api_key=API_KEY)