from __future__ import annotations

from plan_summarizer import (
    DEFAULT_PLAN_PATH,
    summarize_retirement_plan_from_json_string,
)
from Lever_ai import (
    summarize_plan_description_to_narrative,
    assess_law_applicability_to_plan,
)
from supabase_logging import fetch_law_evaluations


def main() -> int:
    # Hardcoded plan path from the repository
    path = DEFAULT_PLAN_PATH

    # Read the retirement plan JSON
    with open(path, "r", encoding="utf-8") as f:
        plan_json = f.read()

    # Summarize to a condensed, machine-friendly snapshot string
    snapshot = summarize_retirement_plan_from_json_string(plan_json)
    print("\n=== Plan Snapshot ===\n")
    print(snapshot)

    # Feed the snapshot into the AI to produce a narrative and completeness score
    narrative = summarize_plan_description_to_narrative(snapshot)
    print("\n=== Planner Narrative ===\n")
    print(narrative.story)
    print("\nCompleteness score:", narrative.completeness_score)

    # Fetch laws with guidance from Supabase and assess applicability
    try:
        rows = fetch_law_evaluations(limit=50)
    except Exception as e:  # noqa: BLE001
        print("\n(Supabase fetch failed)", e)
        rows = []

    results = []
    for r in rows:
        guidance = r.get("guidance")
        print("Guidance: ", guidance)
        input("Press Enter to continue...")
        if not guidance or not isinstance(guidance, str) or not guidance.strip():
            continue
        try:
            app = assess_law_applicability_to_plan(narrative.story, guidance)
            results.append({
                "applicability_score": app.applicability_score,
                "individual_guidance": app.individual_guidance,
                "congress": r.get("congress"),
                "bill": f"{r.get('bill_type')}-{r.get('bill_number')}",
                "title": r.get("title"),
                "importance": r.get("importance"),
                "advantage_score": r.get("advantage_score"),
            })
        except Exception as e:  # noqa: BLE001
            print("(Applicability assessment failed)", e)
            continue

    results.sort(key=lambda x: (x.get("applicability_score") or 0), reverse=True)
    
    print("\n=== Law Applicability Rankings ===\n")
    if not results:
        print("No applicable laws with guidance found.")
    else:
        for idx, it in enumerate(results, 1):
            print(f"{idx}. {it.get('title')} [{it.get('bill')}] -> applicability={it.get('applicability_score')} importance={it.get('importance')} advantage={it.get('advantage_score')}")
            print(f"   Individual guidance: {it.get('individual_guidance')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

