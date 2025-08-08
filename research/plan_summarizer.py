from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Absolute path to the default plan JSON
DEFAULT_PLAN_PATH = "/home/yocto/playground/prova-prova-hackathon-1027/research/Marks_40_Plan.json"
DEFAULT_SCHEMA_PATH = "/home/yocto/playground/prova-prova-hackathon-1027/research/event_schema.json"


# ---------------------------
# Data helpers
# ---------------------------


def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.date() if isinstance(value, datetime) else value
    if isinstance(value, (int, float)):
        # Not expected in this schema, but guard anyway
        try:
            return datetime.fromtimestamp(float(value)).date()
        except (ValueError, OSError, TypeError):
            return None
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(value[:19], fmt)
                return dt.date()
            except ValueError:
                continue
    return None


def _is_amount_key(key: str) -> bool:
    k = key.lower()
    return any(
        token in k
        for token in (
            "amount",
            "salary",
            "money",
            "downpayment",
            "home_value",
            "loan_rate",
            "rate",
            "payment",
            "value",  # fallback, used carefully
        )
    )


def _format_number(value: Any) -> Optional[str]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            fval = float(value)
        except (TypeError, ValueError):
            return None
        # Heuristic: treat values between -1 and 1 (exclusive) as percentages if not 0
        if -1.0 < fval < 1.0 and fval != 0.0:
            pct = fval * 100.0
            return f"{pct:.2f}%"
        if abs(fval) >= 1000:
            return f"${fval:,.0f}"
        if float(fval).is_integer():
            return f"{int(fval)}"
        return f"{fval:.2f}"
    # Strings that are numeric
    if isinstance(value, str):
        v = value.strip().replace(",", "")
        try:
            num = float(v)
        except (TypeError, ValueError):
            return None
        return _format_number(num)
    return None


def _collect_key_amount_snippets(parameters: List[Dict[str, Any]], *, max_items: int = 3) -> List[str]:
    entries: List[Tuple[str, Any]] = []
    # Prefer explicit amount-like keys
    for p in parameters:
        key = str(p.get("type") or p.get("name") or "")
        val = p.get("value")
        if key and _is_amount_key(key):
            fmt = _format_number(val)
            if fmt is not None:
                entries.append((key, fmt))

    # If nothing captured, try any numeric-looking values
    if not entries:
        for p in parameters:
            key = str(p.get("type") or p.get("name") or "value")
            val = p.get("value")
            fmt = _format_number(val)
            if fmt is not None:
                entries.append((key, fmt))

    # Deduplicate preserving order
    seen: set[str] = set()
    deduped: List[Tuple[str, str]] = []
    for k, v in entries:
        if k not in seen:
            seen.add(k)
            deduped.append((k, v))
        if len(deduped) >= max_items:
            break

    return [f"{k}: {v}" for k, v in deduped]


def _get_param_value(parameters: List[Dict[str, Any]], key: str) -> Any:
    for p in parameters:
        if str(p.get("type") or "").lower() == key.lower():
            return p.get("value")
    return None


def _format_value(value: Any) -> str:
    num = _format_number(value)
    if num is not None:
        return num
    if value is None:
        return "null"
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _collect_all_param_snippets(parameters: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for p in parameters:
        key = str(p.get("type") or p.get("name") or "value")
        val = p.get("value")
        lines.append(f"{key}: {_format_value(val)}")
    return lines


def _compute_next_occurrence(
    start: Optional[date],
    end: Optional[date],
    frequency_days: Optional[int],
    today: date,
) -> Optional[date]:
    if start is None:
        return None
    if end is not None and today > end:
        return None
    if frequency_days is None or frequency_days <= 0:
        # One-time event
        return start if start >= today else None

    if start >= today:
        return start

    delta_days = (today - start).days
    cycles = (delta_days + frequency_days - 1) // frequency_days  # ceil
    next_date = start + timedelta(days=cycles * frequency_days)
    if end is not None and next_date > end:
        return None
    return next_date


@dataclass
class EventSummary:
    title: str
    type: str
    start: Optional[date]
    end: Optional[date]
    is_recurring: bool
    next_occurrence: Optional[date]
    key_amounts: List[str]
    description: str
    all_params: List[str]
    all_params_with_desc: List[str]


def _summarize_event(evt: Dict[str, Any], today: date) -> EventSummary:
    title = (evt.get("title") or "").strip() or str(evt.get("type") or "Event").replace("_", " ").title()
    etype = str(evt.get("type") or "Event")
    params: List[Dict[str, Any]] = list(evt.get("parameters") or [])

    start = _parse_date(_get_param_value(params, "start_time"))
    end = _parse_date(_get_param_value(params, "end_time"))
    freq = _get_param_value(params, "frequency_days")
    try:
        frequency_days: Optional[int] = int(freq) if freq is not None else None
    except (TypeError, ValueError):
        frequency_days = None

    next_occ = _compute_next_occurrence(start, end, frequency_days, today)
    key_amounts = _collect_key_amount_snippets(params)
    description = str(evt.get("description") or "").strip()
    all_params = _collect_all_param_snippets(params)
    # Placeholder for enriched params with schema; filled later when schema is available
    all_params_with_desc: List[str] = []

    return EventSummary(
        title=title,
        type=etype,
        start=start,
        end=end,
        is_recurring=bool(evt.get("is_recurring")),
        next_occurrence=next_occ,
        key_amounts=key_amounts,
        description=description,
        all_params=all_params,
        all_params_with_desc=all_params_with_desc,
    )


def _compute_age(birth: date, on_date: date) -> int:
    years = on_date.year - birth.year
    if (on_date.month, on_date.day) < (birth.month, birth.day):
        years -= 1
    return max(0, years)


def _load_event_schema(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _build_param_description_index(schema: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Index of event_type -> param_type -> meta {description, display_name, units}.

    Includes parameters from top-level events and their updating_events (treated as separate event types).
    """
    index: Dict[str, Dict[str, Dict[str, Any]]] = {}
    events = schema.get("events") or []
    for ev in events:
        ev_type = str(ev.get("type") or "").lower()
        if not ev_type:
            continue
        params = ev.get("parameters") or []
        for p in params:
            p_type = str(p.get("type") or "").lower()
            if not p_type:
                continue
            meta = {
                "description": p.get("description"),
                "display_name": p.get("display_name"),
                "units": p.get("parameter_units"),
            }
            index.setdefault(ev_type, {})[p_type] = meta

        # Also index updating events as their own types
        for u in ev.get("updating_events") or []:
            u_type = str(u.get("type") or "").lower()
            if not u_type:
                continue
            for p in u.get("parameters") or []:
                p_type = str(p.get("type") or "").lower()
                if not p_type:
                    continue
                meta = {
                    "description": p.get("description"),
                    "display_name": p.get("display_name"),
                    "units": p.get("parameter_units"),
                }
                index.setdefault(u_type, {})[p_type] = meta

    return index


def _enrich_params_with_schema(
    event_type: str, parameters: List[Dict[str, Any]], param_desc_index: Dict[str, Dict[str, Dict[str, Any]]]
) -> List[str]:
    lines: List[str] = []
    meta_for_event = param_desc_index.get(event_type.lower()) or {}
    for p in parameters:
        key = str(p.get("type") or p.get("name") or "value")
        val = p.get("value")
        meta = meta_for_event.get(key.lower()) or {}
        desc = meta.get("description")
        units = meta.get("units")
        display = meta.get("display_name")

        base = f"{key}: {_format_value(val)}"
        extras: List[str] = []
        if units:
            extras.append(f"units={units}")
        if display:
            extras.append(f"label={display}")
        if desc:
            extras.append(f"desc={desc}")
        if extras:
            base = f"{base} ({'; '.join(extras)})"
        lines.append(base)
    return lines


def summarize_retirement_plan_from_json_string(plan_json: str, *, max_next_events: int = 5) -> str:
    """Produce a condensed, human-readable snapshot of a user's retirement plan.

    Input is a JSON string following the structure of `Mikes_Retirement_Plan.json`.
    The snapshot includes today's date, upcoming events, and condensed lines for all events.

    Returns a single string suitable for display.
    """

    try:
        plan = json.loads(plan_json)
    except json.JSONDecodeError as e:
        return f"Invalid plan JSON: {e}"

    today = date.today()
    events: List[Dict[str, Any]] = list(plan.get("events") or [])

    # Build summaries
    event_summaries: List[EventSummary] = [_summarize_event(evt, today) for evt in events]

    # Load schema and enrich parameter lines with descriptions/units when available
    schema = _load_event_schema(DEFAULT_SCHEMA_PATH)
    param_desc_index: Dict[str, Dict[str, Dict[str, Any]]] = {}
    if schema:
        param_desc_index = _build_param_description_index(schema)
        for idx, evt in enumerate(events):
            enriched = _enrich_params_with_schema(
                event_summaries[idx].type, list(evt.get("parameters") or []), param_desc_index
            )
            event_summaries[idx].all_params_with_desc = enriched

    # Upcoming events sorted by next_occurrence
    upcoming = [e for e in event_summaries if e.next_occurrence is not None]
    upcoming.sort(key=lambda e: e.next_occurrence or date.max)
    upcoming_display = upcoming[:max_next_events]

    # Format header
    header_parts: List[str] = [f"Snapshot as of {today.isoformat()}."]

    # Global plan fields (optional)
    birth_date = plan.get("birth_date")
    view_end = plan.get("view_end_date")
    retirement_goal = plan.get("retirement_goal")
    inflation_rate = plan.get("inflation_rate")

    meta_snippets: List[str] = []
    if birth_date:
        bd = _parse_date(birth_date)
        if bd:
            age_today = _compute_age(bd, today)
            meta_snippets.append(f"Birth date: {bd.isoformat()}; Age: {age_today}")
    if view_end:
        ve = _parse_date(view_end)
        if ve:
            meta_snippets.append(f"Plan horizon: through {ve.isoformat()}")
    if retirement_goal is not None:
        fmt = _format_number(retirement_goal)
        if fmt:
            meta_snippets.append(f"Retirement goal: {fmt}")
    if inflation_rate is not None:
        fmt = _format_number(inflation_rate)
        if fmt:
            meta_snippets.append(f"Assumed inflation: {fmt}")

    if meta_snippets:
        header_parts.append(" ".join(meta_snippets))

    # Upcoming section
    lines: List[str] = []
    lines.append("".join(header_parts))

    if upcoming_display:
        lines.append("\nNext events:")
        for e in upcoming_display:
            date_str = e.next_occurrence.isoformat() if e.next_occurrence else "N/A"
            key_amt = f" | {'; '.join(e.key_amounts)}" if e.key_amounts else ""
            recur = " (recurring)" if e.is_recurring else ""
            desc = f" | desc: {e.description}" if e.description else ""
            age_part = ""
            if birth_date and e.next_occurrence:
                bd = _parse_date(birth_date)
                if bd:
                    age_at_next = _compute_age(bd, e.next_occurrence)
                    age_part = f" | age: {age_at_next}"
            lines.append(f"- {date_str}: {e.title}{recur}{key_amt}{desc}{age_part}")
    else:
        lines.append("\nNext events: None scheduled.")

    # All events detailed enough for downstream extraction
    lines.append("\nPlan events (detailed):")
    # Sort by start date then title
    def _sort_key(es: EventSummary) -> Tuple[date, str]:
        return (es.start or date.max, es.title)

    for e in sorted(event_summaries, key=_sort_key):
        start_str = e.start.isoformat() if e.start else "N/A"
        end_str = e.end.isoformat() if e.end else "N/A"
        recur = " (recurring)" if e.is_recurring else ""
        lines.append(f"- {e.title} [type={e.type}]{recur}")
        lines.append(f"  - Dates: start={start_str}, end={end_str}")
        # Age at start (if birth date and start available)
        bd = _parse_date(birth_date) if birth_date else None
        if bd and e.start:
            lines.append(f"  - Age at start: {_compute_age(bd, e.start)}")
        if e.next_occurrence:
            lines.append(f"  - Next occurrence: {e.next_occurrence.isoformat()}")
        if e.description:
            lines.append(f"  - Description: {e.description}")
        if e.key_amounts:
            lines.append(f"  - Key amounts: {'; '.join(e.key_amounts)}")
        detailed_params = e.all_params_with_desc or e.all_params
        if detailed_params:
            lines.append("  - Parameters:")
            for p in detailed_params:
                lines.append(f"    - {p}")

    # Optional: Envelopes overview for additional numeric context
    envelopes = plan.get("envelopes")
    if isinstance(envelopes, list) and envelopes:
        lines.append("\nEnvelopes:")
        for env in envelopes:
            try:
                name = str(env.get("name") or "Unnamed")
                rate = _format_value(env.get("rate"))
                growth = str(env.get("growth") or "")
                category = str(env.get("category") or "")
                acc_type = str(env.get("account_type") or "")
                parts = [f"name={name}"]
                if category:
                    parts.append(f"category={category}")
                if acc_type:
                    parts.append(f"account_type={acc_type}")
                if rate and rate != "null":
                    parts.append(f"rate={rate}")
                if growth:
                    parts.append(f"growth={growth}")
                lines.append(f"- {'; '.join(parts)}")
            except (TypeError, ValueError):
                continue

    return "\n".join(lines)


def main() -> int:
    try:
        with open(DEFAULT_PLAN_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        print(f"Failed to read file at {DEFAULT_PLAN_PATH}: {e}")
        return 1

    snapshot = summarize_retirement_plan_from_json_string(content)
    print(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

