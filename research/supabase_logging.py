
import os
from typing import Any, Dict, List

from supabase import Client, create_client


TABLE_NAME = "laws_evaluations"
print("Hello from supabse")

# Ensure configuration up-front so failures happen early
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY (or SUPABASE_ANON_KEY) must be set")

# Create client once
_CLIENT: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def insert_law_evaluation(row: Dict[str, Any]) -> None:
    try:
        _CLIENT.table(TABLE_NAME).insert(row).execute()
    except Exception as e:  # noqa: BLE001
        print(f"Failed to insert into {TABLE_NAME}: {e}")
        raise


def upsert_law_evaluation(row: Dict[str, Any]) -> None:
    """Insert or update a law evaluation row keyed by (congress,bill_type,bill_number)."""
    try:
        _CLIENT.table(TABLE_NAME).upsert(row, on_conflict="congress,bill_type,bill_number").execute()
    except Exception as e:  # noqa: BLE001
        print(f"Failed to upsert into {TABLE_NAME}: {e}")
        raise


def fetch_law_evaluations(limit: int = 100, order_desc: bool = True) -> List[Dict[str, Any]]:
    """Fetch recent rows from laws_evaluations.

    Returns a list of dict rows. Raises on failure.
    """
    try:
        q = _CLIENT.table(TABLE_NAME).select("*")
        # Order by created_at if supported in the client version
        try:
            q = q.order("created_at", desc=order_desc)  # type: ignore[arg-type]
        except Exception:
            pass
        resp = q.limit(limit).execute()
        # supabase-py returns resp.data typically; handle dict fallback
        data = getattr(resp, "data", None)
        if data is None and isinstance(resp, dict):
            data = resp.get("data")
        if not isinstance(data, list):
            return []
        return data
    except Exception as e:  # noqa: BLE001
        print(f"Failed to fetch from {TABLE_NAME}: {e}")
        raise

