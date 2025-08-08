from __future__ import annotations

import sys
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel
from supabase_logging import fetch_law_evaluations


class SimpleResult(BaseModel):
    """Structured output: an integer number and a brief explanation."""

    number: int
    explanation: str


class PlanNarrative(BaseModel):
    """Structured output: a planner-style narrative and a completeness score (1-100)."""

    story: str
    completeness_score: int


class ApplicabilityAssessment(BaseModel):
    """Structured output: applicability of a law's guidance to a user's plan."""

    applicability_score: int
    individual_guidance: str


def generate_number_and_explanation(user_input: str, *, model: str = "gpt-5-nano") -> SimpleResult:
    """Call the model with structured outputs to return a number and an explanation.

    Args:
        user_input: The user question or instruction that should yield a numeric answer.
        model: The model name to use. Defaults to "gpt-5-nano".

    Returns:
        SimpleResult: Parsed, schema-validated result with number and explanation.
    """

    client = OpenAI()  # Uses OPENAI_API_KEY from environment

    system_content = (
        "You return structured JSON only. "
        "Compute or extract the numeric answer as an integer in 'number' and provide a short 'explanation'. "
        "If the task is ambiguous, choose a reasonable interpretation and explain briefly."
    )

    # Prefer the modern Responses API if available, else fall back to Chat Completions beta.
    responses_handler = getattr(client, "responses", None)
    if responses_handler is not None and hasattr(responses_handler, "parse"):
        response = responses_handler.parse(  # type: ignore[call-arg]
            model=model,
            input=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_input},
            ],
            text_format=SimpleResult,
        )
        return response.output_parsed  # type: ignore[return-value]

    # Fallback path for older SDKs
    beta = getattr(client, "beta", None)
    if beta is None or not hasattr(beta, "chat"):
        raise RuntimeError(
            "Neither Responses API nor beta.chat is available in the installed openai SDK. Please upgrade the 'openai' package."
        )

    completion = beta.chat.completions.parse(  # type: ignore[attr-defined]
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_input},
        ],
        response_format=SimpleResult,
    )
    return completion.choices[0].message.parsed  # type: ignore[return-value]


def assess_law_applicability_to_plan(
    plan_narrative: str,
    law_guidance: str,
    *,
    model: str = "gpt-5-nano",
) -> ApplicabilityAssessment:
    """Judge how applicable a law's guidance is to the user's plan and tailor next steps.

    Returns:
        ApplicabilityAssessment: with `applicability_score` (1-100) and `individual_guidance` string.
    """

    client = OpenAI()

    system_prompt = (
        "You are a fiduciary financial planner."
        " Using the user's plan narrative and a law's guidance, assess how applicable the guidance is"
        " to the user's actual situation."
        " Score applicability from 1-100 (integer)."
        " Provide a concise, concrete set of next steps tailored to the plan if applicable;"
        " if not applicable, explain briefly why and what information would be needed."
        " Do not fabricate specifics that are not present."
    )

    user_prompt = (
        "Plan Narrative:\n\n"
        f"{plan_narrative}\n\n"
        "Law Guidance:\n\n"
        f"{law_guidance}\n\n"
        "Tasks:\n"
        "1) applicability_score: integer 1-100.\n"
        "2) individual_guidance: concise, personalized steps to implement (or why not applicable)."
    )

    responses_handler = getattr(client, "responses", None)
    if responses_handler is not None and hasattr(responses_handler, "parse"):
        response = responses_handler.parse(  # type: ignore[call-arg]
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=ApplicabilityAssessment,
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
        response_format=ApplicabilityAssessment,
    )
    return completion.choices[0].message.parsed  # type: ignore[return-value]

def summarize_plan_description_to_narrative(
    plan_description: str,
    *,
    model: str = "gpt-5-nano",
) -> PlanNarrative:
    """Turn a user's plan description into a financial-planner-style narrative + completeness score.

    The model returns a structured object with:
      - story: A concise but vivid narrative summarizing the user's life and finances
      - completeness_score: Integer (1-100) indicating how granular/complete the plan appears
    """

    client = OpenAI()

    system_prompt = (
        "You are a seasoned financial planner."
        " Write a concise, professional narrative (3-4 paragraphs) that synthesizes the user's provided plan description into"
        " a story of their life stage, income, expenses, assets, debts, major events (past/upcoming), and retirement trajectory."
        " Include specific numbers and dates whenever they appear."
        " Avoid making up facts, and call out uncertainties or missing data explicitly."
        " Then, assess how complete the input seems on a scale of 1-100, where 100 means the plan is very detailed with amounts, dates, and envelopes,"
        " and 1 means extremely vague."
    )

    user_prompt = (
        "User-provided plan description:\n\n"
        f"{plan_description}\n\n"
        "Tasks:\n"
        "1) Produce a narrative summarizing their financial life and plan using the provided details only.\n"
        "2) Provide a completeness score (1-100) for how granular and comprehensive the plan appears."
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
            text_format=PlanNarrative,
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
        response_format=PlanNarrative,
    )
    return completion.choices[0].message.parsed  # type: ignore[return-value]


def main(argv: list[str]) -> int:
    user_input: Optional[str] = None
    if len(argv) > 1:
        user_input = " ".join(argv[1:])

    if not user_input:
        user_input = "How many letters are in the word 'hello'?"

    result = generate_number_and_explanation(user_input)
    print({"number": result.number, "explanation": result.explanation})

    # Also show some recent law evaluations from Supabase if available
    try:
        rows = fetch_law_evaluations(limit=10)
        if rows:
            print("\nRecent law evaluations (up to 10):")
            for r in rows:
                print({
                    "congress": r.get("congress"),
                    "bill": f"{r.get('bill_type')}-{r.get('bill_number')}",
                    "importance": r.get("importance"),
                    "advantage_score": r.get("advantage_score"),
                    "title": r.get("title"),
                })
        else:
            print("\nNo law evaluations found in Supabase.")
    except Exception as e:  # noqa: BLE001
        print("Supabase fetch failed:", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


