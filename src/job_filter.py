import re
import json
import os

RESUME_PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'resume_profile.json'
)

def load_avoid_titles() -> list[str]:
    """Load titles to avoid from resume_profile.json"""
    try:
        with open(RESUME_PROFILE_PATH, 'r') as f:
            profile = json.load(f)
        return [t.lower().strip() for t in profile.get('avoid_titles', [])]
    except Exception:
        return []
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
    "no f1"
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
        # ── Check Easy Apply field directly ──────────────────
    if job.get('Easy_Apply') is True:
        return True, "Easy Apply"
    
    title       = _normalize(job.get('title', ''))
    description = _normalize(job.get('description', ''))
    combined    = f"{title} {description}"

     # ── Check avoid_titles against job title ─────────────
    avoid_titles = load_avoid_titles()
    for avoid in avoid_titles:
        # Use word boundary to avoid false matches
        pattern = r'\b' + re.escape(avoid) + r'\b'
        if re.search(pattern, title):
            return True, f"avoid title: {avoid}"

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

# # ─────────────────────────────────────────────────────
# # APPLICANT COUNT FILTER
# # Runs AFTER scoring — checks only top 10 job pages
# # Best effort — skips jobs where count cannot be found
# # ─────────────────────────────────────────────────────

# import requests
# from bs4 import BeautifulSoup

# MAX_APPLICANTS = 70      # change this to 10 if you want stricter filter

# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/120.0.0.0 Safari/537.36"
#     ),
#     "Accept-Language": "en-US,en;q=0.9",
# }

# def _get_applicant_count(url: str, source: str) -> int | None:
#     """
#     Try to extract applicant count from job page.
#     Returns count if found, None if not found or blocked.
#     """
#     try:
#         response = requests.get(url, headers=HEADERS, timeout=10)

#         if response.status_code != 200:
#             return None

#         soup = BeautifulSoup(response.text, 'lxml')
#         text = soup.get_text(separator=' ').lower()

#         # ── LinkedIn patterns ─────────────────────────────
#         # "23 applicants", "over 200 applicants", "47 people clicked apply"
#         linkedin_patterns = [
#             r'(\d+)\s+applicants?',
#             r'over\s+(\d+)\s+applicants?',
#             r'(\d+)\s+people\s+clicked\s+apply',
#             r'(\d+)\s+people\s+applied',
#         ]

#         # ── Indeed patterns ───────────────────────────────
#         # "47 applied", "over 200 applied", "1,234 applied"
#         indeed_patterns = [
#             r'([\d,]+)\s+applied',
#             r'over\s+([\d,]+)\s+applied',
#             r'(\d+)\s+candidates',
#         ]

#         patterns = linkedin_patterns if 'linkedin' in source else indeed_patterns

#         for pattern in patterns:
#             match = re.search(pattern, text)
#             if match:
#                 count_str = match.group(1).replace(',', '')
#                 return int(count_str)

#         return None     # count not found on page

#     except Exception:
#         return None     # any error = skip filter for this job


# def filter_by_applicants(
#     jobs: list[dict],
#     max_applicants: int = MAX_APPLICANTS
# ) -> list[dict]:
#     """
#     Check applicant count for each job.
#     Removes jobs with more than max_applicants.
#     Jobs where count cannot be found are KEPT (benefit of doubt).
#     """
#     print(f"\n👥 Checking applicant counts (max allowed: {max_applicants})...")

#     kept     = []
#     removed  = []

#     for job in jobs:
#         url    = job.get('url', '')
#         source = job.get('source', '')
#         title  = job.get('title', '')
#         company= job.get('company', '')

#         count = _get_applicant_count(url, source)

#         if count is None:
#             # Could not fetch count — keep the job
#             print(f"   ⚪ Count unknown  : {title} @ {company} — keeping")
#             job['applicant_count'] = None
#             kept.append(job)

#         elif count <= max_applicants:
#             print(f"   ✅ {count:>4} applicants: {title} @ {company}")
#             job['applicant_count'] = count
#             kept.append(job)

#         else:
#             print(f"   🚫 {count:>4} applicants: {title} @ {company} — removed")
#             job['applicant_count'] = count
#             removed.append(job)

#     print(f"\n   ✅ Kept    : {len(kept)} jobs")
#     print(f"   🚫 Removed : {len(removed)} jobs (>{max_applicants} applicants)\n")

#     return kept
