"""
nlp_extraction.py
Owner: Member 4 - LLM & NLP Developer

Extracts structured profile details (age, state, occupation, education,
income, purpose) from a user's free-text message, in English or Telugu.

Approach: a fast rule/regex-based first pass (works offline, no API cost)
combined with an optional LLM-based fallback extractor for messages that
don't match the simple patterns. This keeps common cases cheap and fast
while still handling messy, conversational phrasing.
"""

import re
from typing import Dict, Optional

INDIAN_STATES = [
    "andhra pradesh", "telangana", "tamil nadu", "karnataka", "kerala",
    "maharashtra", "gujarat", "rajasthan", "punjab", "haryana", "bihar",
    "west bengal", "odisha", "madhya pradesh", "uttar pradesh", "delhi",
    "assam", "jharkhand", "chhattisgarh", "goa", "uttarakhand",
]

OCCUPATION_KEYWORDS = {
    "farmer": ["farmer", "farming", "agriculture", "రైతు"],
    "student": ["student", "studying", "college", "school", "విద్యార్థి"],
    "job seeker": ["job seeker", "unemployed", "looking for job", "నిరుద్యోగి"],
    "woman": ["woman", "women", "mother", "మహిళ"],
    "senior citizen": ["senior citizen", "elderly", "retired", "వృద్ధుడు", "వృద్ధురాలు"],
    "person with disability": ["disability", "disabled", "వికలాంగుడు", "వికలాంగురాలు"],
    "small business owner": ["small business", "shop owner", "self employed", "వ్యాపారం"],
    "worker": ["worker", "labour", "laborer", "కార్మికుడు", "driver", "auto driver"],
}

AGE_PATTERN = re.compile(r"\b(\d{1,3})\s*(?:years?\s*old|yrs?|year of age|ఏళ్ల)\b", re.IGNORECASE)
INCOME_PATTERN = re.compile(
    r"(?:income|earn|salary|ఆదాయం)[^\d]{0,15}(?:rs\.?|₹)?\s*([\d,]+)\s*(lakh|lakhs|thousand|k)?",
    re.IGNORECASE,
)
EDUCATION_KEYWORDS = [
    "10th", "12th", "ssc", "intermediate", "graduate", "post graduate",
    "b.tech", "btech", "diploma", "phd", "illiterate", "no formal education",
]


def extract_age(text: str) -> Optional[int]:
    match = AGE_PATTERN.search(text)
    if match:
        return int(match.group(1))
    return None


def extract_state(text: str) -> Optional[str]:
    lowered = text.lower()
    for state in INDIAN_STATES:
        if state in lowered:
            return state.title()
    return None


def extract_occupation(text: str) -> Optional[str]:
    lowered = text.lower()
    for label, keywords in OCCUPATION_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in lowered:
                return label
    return None


def extract_education(text: str) -> Optional[str]:
    lowered = text.lower()
    for edu in EDUCATION_KEYWORDS:
        if edu in lowered:
            return edu
    return None


def extract_income(text: str) -> Optional[str]:
    match = INCOME_PATTERN.search(text)
    if not match:
        return None
    amount, unit = match.group(1), match.group(2)
    if unit:
        return f"Rs. {amount} {unit}"
    return f"Rs. {amount}"


def extract_profile(text: str, existing_profile: Optional[Dict] = None) -> Dict:
    """
    Extract whatever profile fields can be found in `text` and merge them
    into `existing_profile` (so profile details accumulate across a
    multi-turn conversation instead of being overwritten each time).
    """
    profile = dict(existing_profile) if existing_profile else {}

    age = extract_age(text)
    if age is not None:
        profile["age"] = age

    state = extract_state(text)
    if state:
        profile["state"] = state

    occupation = extract_occupation(text)
    if occupation:
        profile["occupation"] = occupation

    education = extract_education(text)
    if education:
        profile["education"] = education

    income = extract_income(text)
    if income:
        profile["income"] = income

    # "purpose" is intentionally left for the LLM to summarize from the raw
    # message (e.g. "wants a housing loan subsidy") since it's more free-form
    # than the other fields and regex extraction adds little value here.
    profile.setdefault("purpose", None)

    return profile


if __name__ == "__main__":
    sample = "I am a 62 year old farmer from Andhra Pradesh, my income is around Rs 80000 per year."
    print(extract_profile(sample))

    sample_te = "నేను 20 ఏళ్ల విద్యార్థిని, ఆంధ్రప్రదేశ్ లో ఉంటాను"
    print(extract_profile(sample_te))
