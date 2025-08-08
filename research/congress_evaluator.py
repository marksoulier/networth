from __future__ import annotations

from data_collectors.congress_119_laws import (
    list_119th_congress_laws,
    get_item_title,
    fetch_bill_summary,
    process_law_item,
)
from supabase_logging import upsert_law_evaluation

from openai import OpenAI
from pydantic import BaseModel

class LawAssessment(BaseModel):
    importance: int  # 1-100 importance for personal financial decisions
    reason: str  # Brief rationale referencing financial domains


def assess_law_importance(title: str, summary: str, *, model: str = "gpt-5-nano") -> LawAssessment:
    """Use structured outputs to assess a law's importance to personal financial decisions."""
    client = OpenAI()

    system_prompt = (
        "You are a financial planner evaluating public laws for their relevance to personal financial decisions."
        " Rate IMPORTANCE on a 1-100 scale (integer), where 100 = highly impactful to many individuals' decisions"
        " (e.g., taxes, retirement accounts, student loans, health costs, housing, consumer credit), and 1 = negligible."
        " Provide a concise REASON citing the aspects of the summary that influence finances."
        " Avoid fabrications; if uncertain, note that and be conservative."
    )

    user_prompt = (
        f"Title: {title}\n\n"
        f"Summary: {summary}\n\n"
        "Tasks:\n"
        "1) importance: integer 1-100.\n"
        "2) reason: one short sentence connecting the law to personal finance considerations."
    )

    # Prefer Responses API if present
    responses_handler = getattr(client, "responses", None)
    if responses_handler is not None and hasattr(responses_handler, "parse"):
        response = responses_handler.parse(  # type: ignore[call-arg]
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=LawAssessment,
        )
        return response.output_parsed  # type: ignore[return-value]

    # Fallback to beta chat completions parse
    beta = getattr(client, "beta", None)
    if beta is None or not hasattr(beta, "chat"):
        raise RuntimeError(
            "Neither Responses API nor beta.chat is available in the installed openai SDK. Please upgrade the 'openai' package."
        )

    completion = beta.chat.completions.parse(  # type: ignore[attr-defined]
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=LawAssessment,
    )
    return completion.choices[0].message.parsed  # type: ignore[return-value]


class LawFinancialGuidance(BaseModel):
    """Simplified structured output: one score and one narrative string."""

    advantage_score: int  # 1-100 magnitude of advantage if recommendations implemented
    guidance: str         # Single concise paragraph: who is affected, age/demographics/locations, what to do, penalties to avoid, immediate+long-term, include $/% estimates inline


def produce_law_financial_guidance(
    title: str,
    summary: str,
    full_text: str,
    *,
    model: str = "gpt-5-nano",
) -> LawFinancialGuidance:
    """Generate simplified financial guidance for a law using its title, summary, and full text."""
    client = OpenAI()

    system_prompt = (
        "You are a financial planner. Based ONLY on the provided law title, summary, and text,"
        " produce a single concise paragraph that states who is affected (demographics/age/locations),"
        " what to do to take advantage or avoid penalties (immediate and long-term), and include inline rough $ and % savings estimates if feasible."
        " Also produce an integer score 1-100 that reflects the magnitude of financial advantage achievable if the recommendations are implemented."
        " Do not fabricate: if information is insufficient, note it and be conservative."
    )

    user_prompt = (
        f"Title: {title}\n\nSummary: {summary}\n\nFull text (may be long, use selectively):\n{full_text[:20000]}\n\n"
        "Return two fields only: (1) advantage_score (integer 1-100), and (2) guidance (single concise paragraph with all details)."
    )

    responses_handler = getattr(client, "responses", None)
    if responses_handler is not None and hasattr(responses_handler, "parse"):
        response = responses_handler.parse(  # type: ignore[call-arg]
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=LawFinancialGuidance,
        )
        return response.output_parsed  # type: ignore[return-value]

    beta = getattr(client, "beta", None)
    if beta is None or not hasattr(beta, "chat"):
        raise RuntimeError(
            "Neither Responses API nor beta.chat is available in the installed openai SDK. Please upgrade the 'openai' package."
        )
    completion = beta.chat.completions.parse(  # type: ignore[attr-defined]
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=LawFinancialGuidance,
    )
    return completion.choices[0].message.parsed  # type: ignore[return-value]


def main() -> int:
    laws = list_119th_congress_laws()
    print(f"Evaluating {len(laws)} laws from the 119th Congress\n")

    for i, itm in enumerate(laws[:2], 1):
        title = get_item_title(itm) or f"{itm.get('type', '')}-{itm.get('number', '')}"
        bill_type = (itm.get("type") or "").lower()
        bill_num = itm.get("number") or ""
        summary = fetch_bill_summary(bill_type, bill_num) or "No summary available."

        print(f"{i}. {title}")
        print(f"   Summary: {summary}\n")

        assessment = assess_law_importance(title, summary)
        print(f"   Importance: {assessment.importance}")
        print(f"   Reason: {assessment.reason}\n")

        # Prepare base row for optional DB logging
        base_row = {
            "congress": 119,
            "bill_type": bill_type,
            "bill_number": bill_num,
            "title": title,
            "summary": summary,
            "importance": assessment.importance,
            "reason": assessment.reason,
        }

        try:
            upsert_law_evaluation(base_row)
        except Exception as e:
            print("   (Supabase upsert failed for base row)", e)

        if assessment.importance > 60:
            # Pull the entire law and generate financial guidance
            full_text = process_law_item(i, itm) or ""
            if full_text:
                guidance = produce_law_financial_guidance(title, summary, full_text)
                print("   Advantage score:", guidance.advantage_score)
                print("   Guidance:", guidance.guidance, "\n")

                # DB logging with full text stats and guidance
                row = dict(base_row)
                row.update(
                    {
                        "fetched_full_text": True,
                        "full_text_length": len(full_text),
                        "full_text": full_text,
                        "advantage_score": guidance.advantage_score,
                        "guidance": guidance.guidance,
                    }
                )
                try:
                    upsert_law_evaluation(row)
                except Exception as e:
                    print("   (Supabase upsert failed for guidance row)", e)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


