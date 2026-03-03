# ─────────────────────────────────────────────────────────────────────────────
# Daily Job Search Bot — Simplified & Fixed
# Uses: gemini-2.0-flash | 3 countries | Per-country emails | UTF-8 safe
# Set TARGET_COUNTRY env var to: "usa", "india", or "singapore"
# ─────────────────────────────────────────────────────────────────────────────

import google.generativeai as genai
import smtplib
import requests
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# ──────────────────────────────────────────────
# YOUR PROFILE — Edit this section
# ──────────────────────────────────────────────
YOUR_PROFILE = """
## Personal Details:
- Name: Kaavya Sri Ramarapu
- Location: Austin, TX
- Email: ramarapukaavyasri@gmail.com

## Education:
- Master of Science in Electrical Engineering — Texas State University (Aug 2022 – May 2025)
- Research Focus: Environment Emotion Classification to assist Children with ASD
- Courses: Computer Architecture, Machine Learning for Engineering Applications,
  Digital Image Processing, Engineering Economic Analysis, Statistical Methods
- Bachelor of Technology in Electrical and Electronics Engineering
  Jawaharlal Nehru Technological University, Hyderabad (Aug 2016 – Sept 2020)

## Target Roles (apply to ALL three):
1. Product Engineer — hardware/software product bring-up, validation, lifecycle improvement
2. Test & Validation Engineer — PCB testing, embedded systems validation, structured debugging
3. Applied AI Engineer — ML/AI in semiconductor or industrial automation environments

## Also Targeting:
- Graduate Programs (rotational or structured graduate hire programs)
- Rotational Engineering Programs at companies

## Key Skills:
- Languages: Python, C, Linux scripting, SLURM
- ML/AI: PyTorch, TensorFlow, deep learning, GPU-accelerated training, HPC clusters
- Hardware: PCB testing, embedded systems, hardware-software validation
- Tools: Root cause analysis, performance optimization, cross-functional collaboration

## Work Authorization:
- OPT (Optional Practical Training) — authorized to work in USA
- STEM OPT eligible
- Does NOT need H1B sponsorship right now
- NOT a US Citizen or Green Card holder
- NOT currently enrolled as a student (graduated May 2025)

## Experience Level: New Graduate / Entry Level / 0–2 years

## Preferred Company Types:
- Startups and mid-size companies
- Semiconductor: NVIDIA, AMD, Qualcomm, Texas Instruments, Applied Materials,
  Lam Research, KLA, Marvell, Lattice, Microchip, Infineon, NXP
- Industrial Automation: Siemens, ABB, Rockwell Automation, Honeywell, Emerson,
  Cognex, National Instruments, Fanuc, KUKA, Zebra Technologies

## Preferred Locations (USA): Austin TX, Los Angeles CA, Boston MA, Seattle WA, SF CA, Remote

## HARD FILTERS — Skip any job that says:
- "US Citizen only" / "Green Card required" / "Security clearance required"
- "Currently pursuing a degree" / "Must be enrolled"
"""

# ──────────────────────────────────────────────
# COUNTRY CONFIG — 3 countries only
# ──────────────────────────────────────────────
COUNTRY_CONFIG = {
    "usa": {
        "label":     "United States",
        "flag":      "🇺🇸",
        "locations": ["Austin, TX", "Los Angeles, CA", "Boston, MA", "Seattle, WA", "San Francisco, CA", "United States"],
        "indeed_base": "https://www.indeed.com/rss",
    },
    "india": {
        "label":     "India",
        "flag":      "🇮🇳",
        "locations": ["Hyderabad, India", "Bangalore, India"],
        "indeed_base": "https://in.indeed.com/rss",
    },
    "singapore": {
        "label":     "Singapore",
        "flag":      "🇸🇬",
        "locations": ["Singapore"],
        "indeed_base": "https://sg.indeed.com/rss",
    },
}

# ──────────────────────────────────────────────
# ROLE KEYWORDS
# ──────────────────────────────────────────────
ROLE_KEYWORDS = [
    "product engineer new grad",
    "product engineer entry level",
    "test engineer new grad",
    "validation engineer entry level",
    "test validation engineer semiconductor",
    "applied AI engineer semiconductor",
    "AI engineer industrial automation entry level",
    "machine learning engineer semiconductor new grad",
    "rotational engineer program new grad",
    "graduate engineer program",
]

# ──────────────────────────────────────────────
# GREENHOUSE COMPANIES
# ──────────────────────────────────────────────
GREENHOUSE_COMPANIES = [
    "nvidia", "amd", "qualcomm", "applied-materials", "lam-research",
    "kla", "marvell", "lattice-semiconductor", "monolithic-power-systems",
    "boston-dynamics", "automation-anywhere", "zebra-technologies",
    "cognex", "rockwell-automation", "openai", "anthropic", "scale-ai",
    "databricks", "snowflake", "datadog", "stripe", "airbnb",
    "klaviyo", "hubspot", "asana", "okta", "cloudflare",
]

GREENHOUSE_KEYWORDS = [
    "product engineer", "test engineer", "validation engineer",
    "applied ai", "ai engineer", "machine learning engineer",
    "rotational", "graduate program", "new grad", "entry level",
    "automation engineer", "hardware engineer", "semiconductor",
]


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def clean_text(text):
    """Normalize text — replace non-breaking spaces, strip control chars."""
    if not text:
        return ""
    text = text.replace('\xa0', ' ').replace('\u200b', '')
    return text.strip()


def is_fresh(pub_date_str, max_hours=24):
    if not pub_date_str:
        return True
    try:
        pub_dt = parsedate_to_datetime(pub_date_str)
        return (datetime.now(timezone.utc) - pub_dt) <= timedelta(hours=max_hours)
    except Exception:
        return True


# ──────────────────────────────────────────────
# STEP 1: FETCH JOBS
# ──────────────────────────────────────────────

def fetch_indeed(country_key):
    """Fetch from Indeed RSS for the given country."""
    config = COUNTRY_CONFIG[country_key]
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for location in config["locations"]:
        for role in ROLE_KEYWORDS:
            url = (
                f"{config['indeed_base']}"
                f"?q={requests.utils.quote(role)}"
                f"&l={requests.utils.quote(location)}"
                f"&sort=date&fromage=1"
            )
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item"):
                    pub_date = item.findtext("pubDate", "")
                    if not is_fresh(pub_date):
                        continue
                    jobs.append({
                        "title":       clean_text(item.findtext("title", "")),
                        "link":        item.findtext("link", "").strip(),
                        "description": clean_text(item.findtext("description", ""))[:600],
                        "date":        pub_date,
                        "source":      "Indeed",
                        "location":    location,
                        "company":     "",
                    })
                time.sleep(0.5)
            except Exception:
                pass

    print(f"  Indeed ({country_key}): {len(jobs)} fresh jobs")
    return jobs


def fetch_greenhouse():
    """Fetch from Greenhouse public API — no auth needed."""
    jobs = []
    for company in GREENHOUSE_COMPANIES:
        try:
            resp = requests.get(
                f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs",
                timeout=10
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            for job in data.get("jobs", []):
                title = job.get("title", "").lower()
                if not any(kw in title for kw in GREENHOUSE_KEYWORDS):
                    continue
                location = job.get("location", {}).get("name", "") if job.get("location") else ""
                jobs.append({
                    "title":       job.get("title", ""),
                    "link":        job.get("absolute_url", ""),
                    "description": f"Location: {location}",
                    "date":        job.get("updated_at", ""),
                    "source":      "Greenhouse",
                    "location":    location,
                    "company":     company.replace("-", " ").title(),
                })
            time.sleep(0.3)
        except Exception:
            pass
    print(f"  Greenhouse: {len(jobs)} relevant jobs")
    return jobs


def fetch_all_jobs(country_key):
    """Fetch all jobs for a single country."""
    indeed_jobs   = fetch_indeed(country_key)
    greenhouse    = fetch_greenhouse()  # Global — filter by country context later

    # For greenhouse, keep all (Gemini will filter by relevance and location)
    all_jobs = indeed_jobs + greenhouse

    # Deduplicate by link
    seen = set()
    unique = []
    for job in all_jobs:
        if job["link"] not in seen:
            seen.add(job["link"])
            unique.append(job)

    print(f"  Total unique jobs: {len(unique)}")
    return unique


# ──────────────────────────────────────────────
# STEP 2: PRE-FILTER (local, no API call)
# ──────────────────────────────────────────────

def prefilter(jobs, top_n=20):
    """Score and keep the most relevant jobs before calling Gemini."""
    priority = [
        "new grad", "entry level", "graduate", "rotational",
        "product engineer", "test engineer", "validation engineer",
        "applied ai", "machine learning", "semiconductor", "embedded",
        "nvidia", "amd", "qualcomm", "texas instruments", "applied materials",
        "lam research", "kla", "siemens", "honeywell", "rockwell",
        "automation", "hardware", "firmware", "fpga", "pcb",
    ]
    skip = [
        "senior", "staff", "principal", "director", "manager",
        "10+ years", "8+ years", "7+ years", "5+ years",
        "us citizen only", "clearance required",
    ]
    scored = []
    for job in jobs:
        combined = (job.get("title","") + " " + job.get("description","") + " " + job.get("company","")).lower()
        if any(kw in combined for kw in skip):
            continue
        score = sum(1 for kw in priority if kw in combined)
        scored.append((score, job))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [job for _, job in scored[:top_n]]


# ──────────────────────────────────────────────
# STEP 3: GEMINI ANALYSIS
# ──────────────────────────────────────────────

VISA_NOTES = {
    "usa": """
## Work Authorization (USA):
Candidate is on OPT/STEM OPT — authorized to work without employer sponsorship yet.
HARD SKIP: "US Citizen only", "Green Card required", "Security clearance required", "Must be enrolled".
FLAG as VERIFY (do not skip): "No sponsorship" — often means no H1B transfer, OPT may still be fine.
Add sponsorship badge: HIGH = explicitly mentions sponsorship; VERIFY = unclear; SKIP = citizen/GC only (already removed).
""",
    "india": """
## Work Authorization (India):
No visa filtering needed — candidate can work freely in India.
Filter on: role relevance, 0-2 years experience, company type. Skip if 3+ years required.
""",
    "singapore": """
## Work Authorization (Singapore):
Candidate needs Employment Pass (EP). Large MNCs commonly sponsor EP.
Skip jobs saying "Singapore Citizens / PRs only". Note EP requirement per listing.
""",
}


def build_prompt(jobs, country_key):
    jobs_text = ""
    for i, job in enumerate(jobs, 1):
        jobs_text += f"""
---
Job #{i}
Title: {job['title']}
Company: {job.get('company', 'See link')}
Location: {job.get('location', 'Not specified')}
Source: {job['source']}
Link: {job['link']}
Description: {job['description']}
---
"""
    config  = COUNTRY_CONFIG[country_key]
    country = config["label"]

    return f"""
You are an expert job search assistant. Today: {datetime.now().strftime("%B %d, %Y")}.

## Candidate Profile:
{YOUR_PROFILE}

{VISA_NOTES[country_key]}

## Your Tasks:

### STEP 1 — HARD FILTER
Remove jobs matching hard skip criteria. Skip irrelevant or senior roles.

### STEP 2 — SCORE each remaining job (0-100):
- Role match to Product / Test & Validation / Applied AI (40 pts)
- Resume + skills match (30 pts)
- Company type — semiconductor/automation/startup preferred (20 pts)
- Location match (10 pts)

### STEP 3 — KEEP TOP 10 only (highest scoring)

### STEP 4 — OUTPUT: HTML email section for {country} jobs.
For each job produce a card like this (valid HTML, no markdown):

<div style="border:1px solid #e0e0e0; border-radius:10px; padding:20px; margin-bottom:24px; font-family:Arial,sans-serif;">
  <h2 style="color:#1a1a2e; margin:0 0 4px 0;">[Title] [&#128293; if posted within 24h]</h2>
  <h3 style="color:#4a4a8a; margin:0 0 12px 0; font-weight:normal;">[Company] &middot; [Location]</h3>
  <p><strong>Role Type:</strong> [Product Engineer / Test &amp; Validation / Applied AI]</p>
  <p><strong>Match Score:</strong> [X]/100 &mdash; [1-sentence reason]</p>
  <p><strong>Why it fits:</strong> [1-2 sentences on how candidate's background matches]</p>
  <p><strong>Key Requirements:</strong> [req1] &middot; [req2] &middot; [req3]</p>
  <p><strong>Work Auth:</strong> [sponsorship badge and plain English note]</p>
  <a href="[link]" style="display:inline-block; background:#1a1a2e; color:white; padding:8px 18px; border-radius:6px; text-decoration:none;">Apply Now</a>
</div>

Start with a summary line:
<p><strong>Found [X] matching roles</strong> out of [total] listings reviewed for {country}.</p>

If zero jobs match: <p style="color:#888;">No new matching listings found for {country} today.</p>

Use only HTML entities for special characters (no raw emoji in text nodes — use HTML codes like &#128293; for fire emoji). Return ONLY the HTML, no markdown backticks.

## Job Listings:
{jobs_text}
"""


def analyze_with_gemini(jobs, country_key):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")  # Paid tier model — no lite quota issues

    jobs = prefilter(jobs, top_n=20)
    if not jobs:
        return "<p style='color:#888;'>No relevant jobs after pre-filtering.</p>"

    print(f"  Sending {len(jobs)} jobs to Gemini...")
    prompt = build_prompt(jobs, country_key)

    for attempt in range(2):
        try:
            response = model.generate_content(prompt)
            html = response.text
            # Strip markdown code fences if Gemini wraps in ```html ... ```
            html = re.sub(r'^```[a-z]*\n?', '', html.strip())
            html = re.sub(r'\n?```$', '', html.strip())
            # Sanitize any raw non-ASCII that could break email
            html = html.replace('\xa0', '&nbsp;').encode('utf-8', 'replace').decode('utf-8')
            return html
        except Exception as e:
            err = str(e)
            if "429" in err and attempt == 0:
                m = re.search(r'seconds:\s*(\d+)', err)
                wait = int(m.group(1)) + 10 if m else 70
                print(f"  Rate limited — waiting {wait}s then retrying...")
                time.sleep(wait)
            else:
                print(f"  Gemini error: {e}")
                return f"<p style='color:red;'>Gemini analysis failed: {e}</p>"


# ──────────────────────────────────────────────
# STEP 4: SEND EMAIL
# ──────────────────────────────────────────────

def send_email(html_content, country_key):
    sender_email    = os.environ["EMAIL_ADDRESS"]
    sender_password = os.environ["EMAIL_APP_PASSWORD"]
    recipient_email = os.environ["EMAIL_TO"]

    config  = COUNTRY_CONFIG[country_key]
    today   = datetime.now().strftime("%B %d, %Y")
    subject = f"{config['flag']} {config['label']} Job Digest | {today}"

    msg = MIMEMultipart("alternative")
    # Use Header() to safely encode subject with emoji
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"]    = sender_email
    msg["To"]      = recipient_email

    plain = f"Daily engineering job digest for {config['label']}. Open in HTML email client to view."

    full_html = f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif; max-width:720px; margin:auto; padding:20px; background:#f4f4f8;">

  <div style="background:linear-gradient(135deg,#1a1a2e,#4a4a8a); color:white; padding:24px; border-radius:12px; margin-bottom:20px;">
    <h1 style="margin:0 0 6px 0; font-size:22px;">{config['flag']} {config['label']} Engineering Job Digest</h1>
    <p style="margin:0; opacity:0.8; font-size:14px;">Product Engineer &middot; Test &amp; Validation &middot; Applied AI &middot; {today}</p>
  </div>

  <div style="background:#fff8e1; border:1px solid #ffc107; border-radius:8px; padding:12px 18px; margin-bottom:20px; font-size:13px;">
    <strong>OPT Reminder:</strong> "No sponsorship" often means no H1B transfer &mdash; OPT workers frequently still accepted.
    Check <a href="https://www.myvisajobs.com" style="color:#4a4a8a;">myvisajobs.com</a> before applying.
  </div>

  {html_content}

  <div style="text-align:center; color:#aaa; font-size:12px; margin-top:24px; padding-top:16px; border-top:1px solid #ddd;">
    Generated by Gemini AI + GitHub Actions &middot; {today}
  </div>

</body>
</html>"""

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(full_html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

    print(f"  Email sent to {recipient_email}")


# ──────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────

def run():
    # Determine which country to run for (set by GitHub Actions cron via env var)
    country_key = os.environ.get("TARGET_COUNTRY", "usa").lower().strip()

    if country_key not in COUNTRY_CONFIG:
        print(f"Unknown TARGET_COUNTRY: {country_key}. Must be: usa, india, singapore")
        sys.exit(1)

    config = COUNTRY_CONFIG[country_key]
    start  = datetime.now()

    print(f"\n{'='*55}")
    print(f"  Job Search Bot — {config['flag']} {config['label']}")
    print(f"  {start.strftime('%A, %B %d, %Y — %H:%M UTC')}")
    print(f"{'='*55}")

    # Check secrets
    for secret in ["GEMINI_API_KEY", "EMAIL_ADDRESS", "EMAIL_APP_PASSWORD", "EMAIL_TO"]:
        if not os.environ.get(secret):
            print(f"FATAL: Missing secret: {secret}")
            sys.exit(1)

    # Step 1 — Fetch
    print(f"\n--- STEP 1: Fetching jobs for {config['label']} ---")
    jobs = fetch_all_jobs(country_key)
    if not jobs:
        print("No jobs found today.")
        sys.exit(0)

    # Step 2 — Analyze
    print(f"\n--- STEP 2: Gemini analysis ---")
    html = analyze_with_gemini(jobs, country_key)

    # Step 3 — Email
    print(f"\n--- STEP 3: Sending email ---")
    try:
        send_email(html, country_key)
    except Exception as e:
        print(f"Failed to send email: {e}")
        sys.exit(1)

    elapsed = (datetime.now() - start).seconds
    print(f"\n✅ Done in {elapsed}s\n")


if __name__ == "__main__":
    run()
