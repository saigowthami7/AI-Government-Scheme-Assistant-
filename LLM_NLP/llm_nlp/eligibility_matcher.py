"""
eligibility_matcher.py
Owner: Member 4 - LLM & NLP Developer

Given a user's extracted profile and a list of candidate schemes retrieved
by the RAG pipeline (Member 3), this module produces a lightweight
rule-based "possible match" score for each scheme *before* the LLM
generates its final natural-language answer.

This is intentionally simple and transparent (not a black box) — its job
is to catch obvious mismatches (e.g. a 25-year-old being shown a
senior-citizen-only pension scheme) and to surface *why* a scheme looks
like a fit, which also makes the LLM's final answer more grounded.

Final eligibility must always be confirmed against the official source —
this module produces guidance, not a legal determination.
"""

from typing import Dict, List, Optional

TARGET_GROUP_SYNONYMS = {
    "farmer": ["farmers"],
    "student": ["students"],
    "job seeker": ["job seekers"],
    "woman": ["women", "women & children", "families seeking welfare or housing support"],
    "senior citizen": ["senior citizens"],
    "person with disability": ["persons with disabilities"],
    "small business owner": ["small business owners", "workers"],
    "worker": ["workers"],
}


def _age_matches(profile_age: Optional[int], eligibility_text: str) -> Optional[bool]:
    """Very light heuristic: look for '60' + 'above'/'years' patterns etc.
    Returns None when we can't confidently judge age fit (don't block the scheme)."""
    if profile_age is None:
        return None
    eligibility_lower = eligibility_text.lower()
    if "60 years" in eligibility_lower or "aged 60" in eligibility_lower:
        return profile_age >= 60
    if "18-40" in eligibility_lower or "18 to 40" in eligibility_lower:
        return 18 <= profile_age <= 40
    if "below 10 years" in eligibility_lower:
        return profile_age < 10
    if "above 18" in eligibility_lower or "18 years of age" in eligibility_lower:
        return profile_age >= 18
    return None


def score_scheme_for_profile(scheme: Dict, profile: Dict) -> Dict:
    """
    Returns {
        "scheme_id": ...,
        "match_signal": "likely_match" | "possible_match" | "unclear" | "likely_mismatch",
        "reasons": [str, ...]
    }
    """
    reasons = []
    mismatch_found = False
    match_found = False

    # Target group check
    occupation = profile.get("occupation")
    target_groups = [g.lower() for g in scheme.get("target_group", [])]
    if occupation:
        synonyms = TARGET_GROUP_SYNONYMS.get(occupation, [occupation])
        if any(syn.lower() in target_groups for syn in synonyms):
            match_found = True
            reasons.append(f"Target group includes '{occupation}'")

    # State check
    state = profile.get("state")
    scheme_state = scheme.get("state", "")
    if state and scheme_state and scheme_state != "All India":
        if state.lower() != scheme_state.lower():
            mismatch_found = True
            reasons.append(f"Scheme is limited to {scheme_state}, user is in {state}")
        else:
            match_found = True
            reasons.append(f"State matches ({scheme_state})")

    # Age check (best-effort against eligibility text)
    eligibility_text = " ".join(scheme.get("eligibility", []))
    age_result = _age_matches(profile.get("age"), eligibility_text)
    if age_result is True:
        match_found = True
        reasons.append("Age appears to satisfy eligibility criteria")
    elif age_result is False:
        mismatch_found = True
        reasons.append("Age does not appear to satisfy eligibility criteria")

    if mismatch_found:
        signal = "likely_mismatch"
    elif match_found:
        signal = "likely_match"
    elif occupation or state or profile.get("age"):
        signal = "possible_match"
    else:
        signal = "unclear"  # not enough profile info yet

    return {
        "scheme_id": scheme.get("id"),
        "scheme_name": scheme.get("name_en"),
        "match_signal": signal,
        "reasons": reasons,
    }


def rank_schemes(schemes: List[Dict], profile: Dict) -> List[Dict]:
    """
    Score every candidate scheme and sort so the most likely matches are
    first, mismatches last. Used to reorder RAG results before they're
    handed to the LLM, and to help the frontend show a confidence badge.
    """
    priority = {"likely_match": 0, "possible_match": 1, "unclear": 2, "likely_mismatch": 3}
    scored = [score_scheme_for_profile(s, profile) for s in schemes]
    scored.sort(key=lambda r: priority[r["match_signal"]])
    return scored


if __name__ == "__main__":
    sample_scheme = {
        "id": "AP_ASARA005",
        "name_en": "YSR Pension Kanuka (Asara)",
        "target_group": ["senior citizens", "persons with disabilities"],
        "state": "Andhra Pradesh",
        "eligibility": ["Senior citizens aged 60 years and above"],
    }
    sample_profile = {"age": 62, "state": "Andhra Pradesh", "occupation": "senior citizen"}
    print(score_scheme_for_profile(sample_scheme, sample_profile))
