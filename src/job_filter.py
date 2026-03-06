import re
# ─────────────────────────────────────────────────────
# Keywords that indicate you CANNOT apply
# ─────────────────────────────────────────────────────
EXCLUSION_KEYWORDS = [
    # Citizenship only
    "us citizen only",
    "u.s. citizen only",
    "must be a us citizen",
    "must be a u.s. citizen",
    "united states citizen only",
    "citizenship required",
    "american citizen only",

    # Security clearance (requires citizenship)
    "security clearance required",
    "secret clearance",
    "top secret",
    "ts/sci",
    "dod clearance",
    "active clearance",
    "clearance required",

    # Green card only
    "green card required",
    "green card only",
    "permanent resident only",
    "gc required",
    "gc only",

    # Explicitly blocks OPT
    "no opt",
    "no stem opt",
    "opt not accepted",
    "opt not eligible",
    "stem opt not accepted",
    "cannot accept opt",
    "no f-1",
    "no f1",

    # Easy apply — low quality listings
    "easy apply",
]

# ─────────────────────────────────────────────────────
# Safe phrases — these override exclusions
# OPT/STEM OPT friendly = good for you
# H1B sponsorship = nice but not required
# ─────────────────────────────────────────────────────
SAFE_PHRASES = [
    # OPT / STEM OPT explicitly welcome
    "opt",
    "stem opt",
    "f-1",
    "f1 visa",
    "opt candidates",
    "opt welcome",
    "stem opt welcome",
    "open to opt",
    "accepts opt",
    "all work authorizations",
    "all visa types",
    "any work authorization",
    "authorized to work",
    "equal opportunity",

    # Sponsorship available (bonus but not required)
    "willing to sponsor",
    "we will sponsor",
    "sponsorship available",
    "visa sponsorship available",
    "h1b sponsor",
    "h-1b sponsor",
    "we sponsor",
    "open to sponsoring",

    # Graduate / rotational programs
    "new grad",
    "new graduate",
    "rotational program",
    "graduate program",
    "associate program",
    "early career",
    "campus hire",
    "university hire",
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
