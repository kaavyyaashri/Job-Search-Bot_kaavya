import re

# ─────────────────────────────────────────────────────
# Keywords that indicate you CANNOT apply for this role
# (work authorization restrictions)
# ─────────────────────────────────────────────────────
EXCLUSION_KEYWORDS = [
    # Citizenship
    "us citizen",
    "u.s. citizen",
    "united states citizen",
    "must be a citizen",
    "citizenship required",
    "american citizen",

    # Security clearance (usually requires citizenship)
    "security clearance",
    "secret clearance",
    "top secret",
    "ts/sci",
    "dod clearance",
    "government clearance",
    "clearance required",

    # Green card
    "green card",
    "permanent resident only",
    "gc required",

    # OPT / STEM OPT
    "no opt",
    "no stem opt",
    "opt not accepted",
    "stem opt not",
    "cannot sponsor opt",

    # Sponsorship
    "no sponsorship",
    "will not sponsor",
    "unable to sponsor",
    "not able to sponsor",
    "cannot sponsor",
    "sponsorship not available",
    "sponsorship is not available",
    "does not offer sponsorship",
    "no visa sponsorship",
    "visa sponsorship not provided",

    # Easy Apply (low quality listings)
    "easy apply",
]

# ─────────────────────────────────────────────────────
# Keywords that are FINE — don't filter these out
# even if they contain "sponsor" or similar words
# ─────────────────────────────────────────────────────
SAFE_PHRASES = [
    "willing to sponsor",
    "we sponsor",
    "we will sponsor",
    "sponsorship available",
    "visa sponsorship available",
    "open to sponsoring",
    "h1b sponsor",
    "h-1b sponsor",
]

def _normalize(text: str) -> str:
    """Lowercase and collapse whitespace for consistent matching"""
    return re.sub(r'\s+', ' ', text.lower().strip())

def is_job_excluded(job: dict) -> tuple[bool, str]:
    """
    Returns (should_exclude, reason).
    Checks title + description for exclusion keywords.
    """
    title       = _normalize(job.get('title', ''))
    description = _normalize(job.get('description', ''))
    combined    = f"{title} {description}"

    # Check if any safe phrase is present first
    for safe in SAFE_PHRASES:
        if safe in combined:
            return False, ""

    # Check for exclusion keywords
    for keyword in EXCLUSION_KEYWORDS:
        if keyword in combined:
            return True, keyword

    return False, ""

def filter_jobs(jobs: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Split jobs into (eligible, excluded).
    Logs what was filtered and why.
    """
    eligible = []
    excluded = []

    for job in jobs:
        should_exclude, reason = is_job_excluded(job)
        if should_exclude:
            job['excluded_reason'] = reason
            excluded.append(job)
        else:
            eligible.append(job)

    return eligible, excluded
