# Job Search automate code with the help of Claude

import anthropic
import smtplib
import requests
import os
import xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ──────────────────────────────────────────────
# YOUR PROFILE — Edit this section
# ──────────────────────────────────────────────
YOUR_PROFILE = """
## Target Roles (apply to ALL three):
1. Product Engineer
2. Test & Validation Engineer
3. Applied AI Engineer — focused on Semiconductor or Industrial Automation companies

## Also Targeting:
- Graduate Programs (rotational or structured graduate hire programs)
- Rotational Engineering Programs at companies

## Education:
- Masters degree (Engineering or CS related)
- New Graduate / Recently graduated

## Work Authorization:
- OPT (Optional Practical Training)
- STEM OPT eligible
- Does NOT require H1B sponsorship
- NOT a US Citizen or Green Card holder
- NOT currently pursuing a degree (already graduated)
- Open to companies that are OPT/STEM OPT friendly
- Future sponsorship is flexible and company-dependent — not a priority right now

## Experience Level:
- New Graduate / Entry Level
- 0–2 years experience

## Preferred Company Types:
- Startups and mid-size companies
- Semiconductor companies (e.g., NVIDIA, AMD, Qualcomm, Texas Instruments, Applied Materials, Lam Research, KLA, Marvell)
- Industrial Automation companies (e.g., Siemens, ABB, Rockwell Automation, Honeywell, Emerson, Cognex, National Instruments)
- Companies with structured new grad / rotational programs

## Preferred Locations (in order of preference):
- Austin, TX
- Los Angeles, CA
- Boston, MA
- Seattle, WA
- San Francisco, CA
- Remote (USA-based) — also acceptable

## HARD FILTERS — Skip any job that says:
- "US Citizen only"
- "Green Card required"
- "Must be authorized to work without sponsorship" (this blocks OPT too at some companies)
- "Security clearance required"
- "Currently pursuing a degree" (already graduated)
- "Active student enrollment required"
"""

# ──────────────────────────────────────────────
# LOCATIONS — Edit this to change search cities
# ──────────────────────────────────────────────
SEARCH_LOCATIONS = {
    "usa": [
        "Austin, TX",
        "Los Angeles, CA",
        "Boston, MA",
        "Seattle, WA",
        "San Francisco, CA",
        "United States",        # catches remote + nationwide posts
    ],
    "india": [
        "Hyderabad, India",
        "Bangalore, India",
    ],
    "singapore": [
        "Singapore",
    ],
    "ireland": [
        "Dublin, Ireland",
    ],
}

# ── Toggle countries ON/OFF here ──────────────
# Set to True to search, False to skip
ACTIVE_COUNTRIES = {
    "usa":       True,
    "india":     True,
    "singapore": True,
    "ireland":   True,
}

# ──────────────────────────────────────────────
# ROLE KEYWORDS — Edit to add/remove role searches
# ──────────────────────────────────────────────
ROLE_KEYWORDS = [
    "product engineer new grad",
    "product engineer entry level",
    "product engineer rotational program",
    "test engineer new grad",
    "validation engineer entry level",
    "test validation engineer semiconductor",
    "test validation engineer industrial automation",
    "applied AI engineer semiconductor",
    "AI engineer industrial automation entry level",
    "machine learning engineer semiconductor new grad",
    "rotational engineer program new grad",
    "graduate engineer program",
    "engineering rotational program",
]

# ──────────────────────────────────────────────
# AUTO-BUILD SEARCH QUERIES from above settings
# ──────────────────────────────────────────────
SEARCH_QUERIES = []

for country, is_active in ACTIVE_COUNTRIES.items():
    if is_active:
        for location in SEARCH_LOCATIONS[country]:
            for role in ROLE_KEYWORDS:
                SEARCH_QUERIES.append({"q": role, "l": location})

# ──────────────────────────────────────────────
# COMPANIES KNOWN TO SPONSOR — Used as a bonus filter
# ──────────────────────────────────────────────
KNOWN_SPONSORS = [
    "Google", "Microsoft", "Amazon", "Meta", "Apple", "Salesforce",
    "Stripe", "Airbnb", "Lyft", "Uber", "DoorDash", "Coinbase",
    "Databricks", "Snowflake", "Figma", "Notion", "Linear", "Vercel",
    "OpenAI", "Anthropic", "Scale AI", "Palantir", "Twilio", "MongoDB",
    "Atlassian", "Asana", "HubSpot", "Zendesk", "Okta", "Cloudflare",
    "Datadog", "HashiCorp", "Splunk", "New Relic", "PagerDuty",
]

# ──────────────────────────────────────────────
# STEP 1: Fetch jobs for ALL countries
# ──────────────────────────────────────────────
import time
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# ──────────────────────────────────────────────
# COUNTRY-SPECIFIC JOB BOARD RSS URLS
# ──────────────────────────────────────────────

def build_indeed_urls(queries):
    """Build Indeed RSS URLs — works for USA, India, Singapore, Ireland"""
    urls = []
    for query in queries:
        base = "https://www.indeed.com/rss"
        # Use country-specific Indeed domains
        location = query["l"].lower()
        if "india" in location:
            base = "https://in.indeed.com/rss"
        elif "singapore" in location:
            base = "https://sg.indeed.com/rss"
        elif "ireland" in location or "dublin" in location:
            base = "https://ie.indeed.com/rss"

        url = (
            f"{base}"
            f"?q={requests.utils.quote(query['q'])}"
            f"&l={requests.utils.quote(query['l'])}"
            f"&sort=date"
            f"&fromage=1"  # Posted within last 1 day (freshest RSS allows)
        )
        urls.append({"url": url, "source": "Indeed", "country": query["l"]})
    return urls


def build_greenhouse_urls():
    """
    Greenhouse is a hiring platform used by many startups and tech companies.
    Their API is public — no key needed. Returns very fresh listings.
    These are companies in your target sectors known to hire new grads + OPT friendly.
    """
    companies = [
        # Semiconductor & Hardware
        "nvidia", "amd", "qualcomm", "applied-materials", "lam-research",
        "kla", "marvell", "lattice-semiconductor", "monolithic-power-systems",
        # Industrial Automation & Robotics
        "boston-dynamics", "automation-anywhere", "zebra-technologies",
        "cognex", "national-instruments", "rockwell-automation",
        # AI & Software (product engineering focus)
        "openai", "anthropic", "scale-ai", "cohere", "mistral",
        "databricks", "snowflake", "datadog", "figma", "notion",
        "linear", "vercel", "stripe", "airbnb", "doordash",
        # Mid-size startups with rotational programs
        "klaviyo", "hubspot", "asana", "okta", "cloudflare", "hashicorp",
    ]
    urls = []
    for company in companies:
        urls.append({
            "url": f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs",
            "source": "Greenhouse",
            "company": company,
        })
    return urls


def build_wellfound_urls(queries):
    """Wellfound (AngelList) — great for startups, has public RSS"""
    role_map = {
        "product engineer": "product-engineer",
        "test engineer": "test-engineer",
        "applied ai": "ai-engineer",
        "validation engineer": "validation-engineer",
    }
    urls = []
    for role_key, role_slug in role_map.items():
        urls.append({
            "url": f"https://wellfound.com/role/r/{role_slug}?utm_source=rss",
            "source": "Wellfound",
            "role": role_key,
        })
    return urls


# ──────────────────────────────────────────────
# FRESHNESS FILTER
# ──────────────────────────────────────────────

def is_fresh_enough(pub_date_str, max_hours=24):
    """
    Returns True if the job was posted within max_hours.
    RSS feeds refresh every few hours so 24h is the practical minimum.
    We keep today's jobs and skip anything older.
    """
    if not pub_date_str:
        return True  # If no date, keep it (better safe than miss)
    try:
        pub_dt = parsedate_to_datetime(pub_date_str)
        now = datetime.now(timezone.utc)
        age = now - pub_dt
        return age <= timedelta(hours=max_hours)
    except Exception:
        return True  # If unparseable, keep it


# ──────────────────────────────────────────────
# FETCH FROM INDEED RSS
# ──────────────────────────────────────────────

def fetch_from_indeed(queries):
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    urls = build_indeed_urls(queries)

    for entry in urls:
        try:
            response = requests.get(entry["url"], headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"  ⚠️  Indeed returned {response.status_code} for {entry['country']}")
                continue

            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            fresh_count = 0

            for item in items:
                pub_date = item.findtext("pubDate", "")
                if not is_fresh_enough(pub_date, max_hours=24):
                    continue  # Skip old listings

                jobs.append({
                    "title":       item.findtext("title", "").strip(),
                    "link":        item.findtext("link", "").strip(),
                    "description": item.findtext("description", "").strip()[:800],
                    "date":        pub_date,
                    "source":      "Indeed",
                    "location":    entry["country"],
                })
                fresh_count += 1

            print(f"  ✅ Indeed [{entry['country']}] → {fresh_count} fresh jobs")
            time.sleep(1)  # Be polite to Indeed's servers

        except Exception as e:
            print(f"  ❌ Indeed error for {entry['country']}: {e}")

    return jobs


# ──────────────────────────────────────────────
# FETCH FROM GREENHOUSE API
# ──────────────────────────────────────────────

def fetch_from_greenhouse():
    jobs = []
    urls = build_greenhouse_urls()

    # Keywords to filter relevant roles from Greenhouse
    relevant_keywords = [
        "product engineer", "test engineer", "validation engineer",
        "applied ai", "ai engineer", "machine learning engineer",
        "rotational", "graduate program", "new grad", "entry level",
        "automation engineer", "hardware engineer", "semiconductor",
    ]

    for entry in urls:
        try:
            response = requests.get(entry["url"], timeout=10)
            if response.status_code != 200:
                continue

            data = response.json()
            all_jobs = data.get("jobs", [])

            for job in all_jobs:
                title = job.get("title", "").lower()

                # Only keep jobs with relevant titles
                if not any(kw in title for kw in relevant_keywords):
                    continue

                location = ""
                if job.get("location"):
                    location = job["location"].get("name", "")

                jobs.append({
                    "title":       job.get("title", ""),
                    "link":        job.get("absolute_url", ""),
                    "description": f"Location: {location}. " + str(job.get("metadata", ""))[:400],
                    "date":        job.get("updated_at", ""),
                    "source":      "Greenhouse",
                    "location":    location,
                    "company":     entry["company"],
                })

            time.sleep(0.5)

        except Exception as e:
            # Many companies won't have a Greenhouse board — that's fine, skip silently
            pass

    print(f"  ✅ Greenhouse → {len(jobs)} relevant jobs found across all companies")
    return jobs


# ──────────────────────────────────────────────
# FETCH FROM GLASSDOOR RSS
# ──────────────────────────────────────────────

def fetch_from_glassdoor(queries):
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # Glassdoor RSS — limited but free
    role_samples = [
        "product+engineer", "test+engineer",
        "validation+engineer", "applied+ai+engineer"
    ]

    for role in role_samples:
        url = f"https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword={role}&sc.keyword={role}&locT=N&locId=1&jobType=&context=Jobs&rsRedir=false"
        # Note: Glassdoor doesn't have a true RSS anymore — we use their job search page
        # and fall back to Indeed for Glassdoor-listed jobs (Indeed aggregates them)
        pass

    print(f"  ℹ️  Glassdoor: Using Indeed as aggregator (Glassdoor RSS deprecated in 2023)")
    return jobs  # Indeed already captures Glassdoor-listed jobs


# ──────────────────────────────────────────────
# COUNTRY-SPECIFIC BOARDS
# ──────────────────────────────────────────────

def fetch_country_specific():
    """
    Extra job boards for India, Singapore, Ireland
    that go beyond Indeed's international coverage
    """
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    extra_feeds = [
        # Ireland — IrishJobs.ie RSS
        {
            "url": "https://www.irishjobs.ie/TalentAlert/TalentAlert.aspx?SectorID=18&Keyword=engineer",
            "source": "IrishJobs",
            "location": "Dublin, Ireland"
        },
        # Singapore — JobsDB RSS
        {
            "url": "https://sg.jobsdb.com/j?q=product+engineer&l=singapore",
            "source": "JobsDB",
            "location": "Singapore"
        },
        # India — Naukri doesn't have public RSS but Indeed India covers it well
        # Greenhouse also has India offices for many companies above
    ]

    for feed in extra_feeds:
        try:
            response = requests.get(feed["url"], headers=headers, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall(".//item")
                for item in items:
                    pub_date = item.findtext("pubDate", "")
                    if not is_fresh_enough(pub_date, max_hours=24):
                        continue
                    jobs.append({
                        "title":       item.findtext("title", "").strip(),
                        "link":        item.findtext("link", "").strip(),
                        "description": item.findtext("description", "").strip()[:800],
                        "date":        pub_date,
                        "source":      feed["source"],
                        "location":    feed["location"],
                    })
                print(f"  ✅ {feed['source']} [{feed['location']}] → {len(jobs)} jobs")
        except Exception as e:
            print(f"  ⚠️  {feed['source']} unavailable: {e}")

    return jobs


# ──────────────────────────────────────────────
# MASTER FETCH FUNCTION — calls all sources
# ──────────────────────────────────────────────

def fetch_all_jobs():
    print("\n📡 Fetching jobs from all sources...\n")
    all_jobs = []

    # Build queries only for active countries
    active_queries = []
    for country, is_active in ACTIVE_COUNTRIES.items():
        if is_active:
            for location in SEARCH_LOCATIONS[country]:
                for role in ROLE_KEYWORDS:
                    active_queries.append({"q": role, "l": location})

    # Fetch from each source
    all_jobs += fetch_from_indeed(active_queries)
    all_jobs += fetch_from_greenhouse()
    all_jobs += fetch_country_specific()

    # Deduplicate by link
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = job.get("link", job.get("title", ""))
        if key and key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    print(f"\n📊 Total unique fresh jobs fetched: {len(unique_jobs)}")
    return unique_jobs

# ──────────────────────────────────────────────
# STEP 2: Filter and enrich jobs using Claude
# ──────────────────────────────────────────────

# Resume summaries for each role — Claude uses these to score match
# Paste a short summary of each resume here (3-5 bullet points each)
# ──────────────────────────────────────────────
# RESUME LOADER — reads actual .docx files
# ──────────────────────────────────────────────
import os
from docx import Document

# Map role categories to resume filenames in the /resumes folder
RESUME_FILES = {
    "product_engineer":         "resumes/product_engineer.docx",
    "test_validation_engineer": "resumes/test_validation_engineer.docx",
    "applied_ai_engineer":      "resumes/applied_ai_engineer.docx",
}

def load_resume(role_category):
    """
    Reads the .docx resume file for the given role category.
    Returns extracted text, or a fallback message if file not found.
    """
    filepath = RESUME_FILES.get(role_category)

    if not filepath:
        return "Resume not available for this role category."

    if not os.path.exists(filepath):
        print(f"  ⚠️  Resume file not found: {filepath}")
        return f"Resume file missing: {filepath} — please add it to the repo."

    try:
        doc = Document(filepath)
        full_text = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                full_text.append(text)

        # Also extract text from tables (some resumes use table layouts)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        full_text.append(cell_text)

        extracted = "\n".join(full_text)

        # Trim to ~2000 chars to stay within Claude token limits
        # Keeps the most important top section of your resume
        if len(extracted) > 2000:
            extracted = extracted[:2000] + "\n... [resume trimmed for brevity]"

        print(f"  ✅ Loaded resume: {filepath} ({len(extracted)} chars)")
        return extracted

    except Exception as e:
        print(f"  ❌ Error reading resume {filepath}: {e}")
        return f"Could not read resume file: {e}"


# Pre-load all resumes once at startup (not on every job iteration)
print("\n📄 Loading resume files...")
LOADED_RESUMES = {
    role: load_resume(role)
    for role in RESUME_FILES.keys()
}
print("✅ Resumes loaded\n")


def detect_role_category(job_title, job_description):
    """Map a job listing to one of the three target role categories"""
    title_lower = job_title.lower()
    desc_lower = job_description.lower()
    combined = title_lower + " " + desc_lower

    if any(kw in combined for kw in [
        "test engineer", "validation engineer", "test & validation",
        "test and validation", "hw test", "hardware test", "software test",
        "quality engineer", "reliability engineer", "verification"
    ]):
        return "test_validation_engineer"

    elif any(kw in combined for kw in [
        "applied ai", "ai engineer", "machine learning engineer",
        "ml engineer", "ai applications", "deep learning engineer",
        "computer vision engineer", "nlp engineer"
    ]):
        return "applied_ai_engineer"

    else:
        return "product_engineer"  # default category


def detect_country_context(location_str):
    """Return country context so Claude applies the right visa filters"""
    loc = location_str.lower()
    if any(x in loc for x in ["india", "hyderabad", "bangalore", "bengaluru"]):
        return "india"
    elif "singapore" in loc:
        return "singapore"
    elif any(x in loc for x in ["ireland", "dublin"]):
        return "ireland"
    else:
        return "usa"  # default


def build_claude_prompt(jobs_batch, country_context):
    """
    Build the filtering + enrichment prompt for Claude.
    Different visa/authorization instructions per country.
    """

    # ── Visa filter instructions vary by country ──────────────
    if country_context == "usa":
        visa_instructions = """
## Visa / Work Authorization Filters (USA ONLY — apply strictly):
The candidate is on OPT (Optional Practical Training) / STEM OPT.
This means:
- They ARE authorized to work in the USA during OPT period (no employer sponsorship needed YET)
- They DO NOT need H1B sponsorship right now
- They ARE NOT a US Citizen or Green Card holder
- They ARE NOT currently enrolled as a student (already graduated)

### HARD SKIP — Remove any job that says ANY of the following:
- "US Citizen only" or "US Citizen required"
- "Green Card required" or "Permanent Resident required"
- "Security clearance required" or "Must hold active clearance"
- "Currently pursuing a degree" or "Must be enrolled in university"
- "Active student enrollment required"
- "No international students"

### FLAG as ⚠️ VERIFY (do NOT auto-skip — candidate decides):
- "No sponsorship available" or "We do not sponsor visas"
  → Reason: This often means no H1B TRANSFER, not necessarily blocking OPT workers
  → Claude should note: "Says no sponsorship — may still accept OPT. Verify directly."

### SPONSORSHIP LIKELIHOOD BADGE (for USA jobs only):
- ✅ HIGH — Company explicitly says "visa sponsorship available" OR is on known H1B sponsor list
- ⚠️ VERIFY — No mention of sponsorship either way, or says "no sponsorship" (OPT may still be fine)
- ❌ SKIP — Explicitly says "US Citizen only" or "Green Card required" (already filtered out above)
"""
    elif country_context == "india":
        visa_instructions = """
## Work Authorization (INDIA):
- No visa filtering needed — candidate can work freely in India
- Focus filtering on: role relevance, experience level (new grad / 0-2 years), company type
- Flag if job requires 3+ years experience (skip those)
- Prioritize: MNCs with India offices, semiconductor companies, industrial automation firms, startups
"""
    elif country_context == "singapore":
        visa_instructions = """
## Work Authorization (SINGAPORE):
- Candidate would need an Employment Pass (EP) or S Pass for Singapore
- Flag jobs at companies known to hire international candidates
- Large MNCs and tech companies in Singapore commonly sponsor EP
- Skip jobs that say "Singapore Citizens / PRs only"
- Note EP requirement in each listing
"""
    elif country_context == "ireland":
        visa_instructions = """
## Work Authorization (IRELAND / EU):
- Candidate would need a Critical Skills Employment Permit or General Employment Permit
- Engineering roles often qualify for Critical Skills permit
- Large tech companies in Dublin (Google, Meta, LinkedIn, Amazon, Microsoft) regularly sponsor
- Skip if "EU citizens only" or "Right to work in Ireland required without sponsorship"
- Note permit requirement in each listing
"""

    # ── Build jobs text block ──────────────────────────────────
    jobs_text = ""
    for i, job in enumerate(jobs_batch, 1):
        role_cat = detect_role_category(job["title"], job["description"])
        resume = LOADED_RESUMES.get(role_cat, "Resume not available")
        jobs_text += f"""
---
Job #{i}
Title: {job['title']}
Company: {job.get('company', 'See link')}
Location: {job.get('location', 'Not specified')}
Source: {job['source']}
Posted: {job.get('date', 'Unknown')}
Link: {job['link']}
Description: {job['description']}
Detected Role Category: {role_cat.replace('_', ' ').title()}
Candidate Resume for this Role:
{resume}
---
"""

    prompt = f"""
You are an expert job search assistant helping a Masters graduate find engineering roles.
Today's date: {datetime.now().strftime("%B %d, %Y")}

## Candidate Profile:
{YOUR_PROFILE}

{visa_instructions}

## Role Matching Instructions:
The candidate is targeting THREE role types. Match each job to one:
1. **Product Engineer** — building and owning product features, full-stack, platform
2. **Test & Validation Engineer** — hardware/software testing, validation, QA, reliability
3. **Applied AI Engineer** — ML/AI applications in semiconductor or industrial automation

Also flag if a job is:
- 🎓 **Graduate Program** — structured new grad rotational or graduate hire program
- 🔄 **Rotational Program** — multi-team rotation program for new grads

## Company Priority Flags:
Give extra priority to these sectors:
- Semiconductor companies (NVIDIA, AMD, Qualcomm, TI, Applied Materials, Lam Research, KLA, Marvell, etc.)
- Industrial Automation (Siemens, ABB, Rockwell Automation, Honeywell, Cognex, Emerson, Fanuc, etc.)
- Startups and mid-size tech companies (not just FAANG)

## Your Tasks:

### STEP 1 — HARD FILTER
Remove jobs that match the hard skip criteria above.
If fewer than 5 jobs remain after filtering, keep ⚠️ VERIFY ones too.

### STEP 2 — SCORE each remaining job (0–100) based on:
- Role match to one of the 3 target roles (40 pts)
- Resume match — how well candidate's background fits (30 pts)
- Company type match — semiconductor/automation/startup preferred (20 pts)
- Location match to preferred cities (10 pts)

### STEP 3 — ENRICH each job that scores 40 or above with:
1. **Job Title** + **Role Category** (Product / Test & Validation / Applied AI)
2. **Company Name** + sector (Semiconductor / Automation / Startup / Tech)
3. **Team or Department** hiring (if mentioned in description)
4. **Top 3 Requirements** from the listing
5. **Match Score** out of 100 with a 1-sentence reason
6. **Resume Fit** — 1 sentence on how candidate's background fits
7. **Company Overview** — what they do, size, notable products (2-3 sentences)
8. **Work Authorization Note** — based on country context above
9. **Recruiter / Contact Email** — if found in listing (else write "Not listed")
10. **Application Link**
11. **Program Flag** — Graduate Program 🎓 / Rotational 🔄 / Standard Role (pick one)

### STEP 4 — SORT results:
- For USA: Sort by sponsorship likelihood first (✅ HIGH → ⚠️ VERIFY), then by match score
- For other countries: Sort by match score descending

### OUTPUT FORMAT:
Return ONLY clean HTML — no markdown, no code fences, no preamble text.
Use exactly this card template for each job:

<div style="border:1px solid #e0e0e0; border-radius:10px; padding:20px; margin-bottom:24px; font-family:Arial,sans-serif; background:#ffffff;">

  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
    <div>
      <h2 style="color:#1a1a2e; margin:0 0 4px 0; font-size:18px;">[Job Title]</h2>
      <h3 style="color:#4a4a8a; margin:0; font-size:15px; font-weight:normal;">[Company Name] · [Sector Badge]</h3>
    </div>
    <div style="text-align:right;">
      <span style="background:#f0f0ff; color:#4a4a8a; padding:4px 10px; border-radius:20px; font-size:13px; font-weight:bold;">[Role Category]</span><br>
      <span style="font-size:13px; color:#666; margin-top:4px; display:block;">[Program Flag if applicable]</span>
    </div>
  </div>

  <hr style="border:none; border-top:1px solid #f0f0f0; margin:12px 0;">

  <table style="width:100%; font-size:14px; border-collapse:collapse;">
    <tr>
      <td style="padding:4px 8px 4px 0; color:#888; width:160px;">📍 Location</td>
      <td style="padding:4px 0;">[Location]</td>
    </tr>
    <tr>
      <td style="padding:4px 8px 4px 0; color:#888;">🏢 Team / Dept</td>
      <td style="padding:4px 0;">[Team or Department]</td>
    </tr>
    <tr>
      <td style="padding:4px 8px 4px 0; color:#888;">📋 Top Requirements</td>
      <td style="padding:4px 0;">[req1] · [req2] · [req3]</td>
    </tr>
    <tr>
      <td style="padding:4px 8px 4px 0; color:#888;">🎯 Match Score</td>
      <td style="padding:4px 0;"><strong>[Score]/100</strong> — [1 sentence reason]</td>
    </tr>
    <tr>
      <td style="padding:4px 8px 4px 0; color:#888;">📄 Resume Fit</td>
      <td style="padding:4px 0;">[1 sentence]</td>
    </tr>
    <tr>
      <td style="padding:4px 8px 4px 0; color:#888;">🏭 Company</td>
      <td style="padding:4px 0;">[2-3 sentence overview]</td>
    </tr>
    <tr>
      <td style="padding:4px 8px 4px 0; color:#888;">🛂 Work Auth</td>
      <td style="padding:4px 0;">[Sponsorship badge + note]</td>
    </tr>
    <tr>
      <td style="padding:4px 8px 4px 0; color:#888;">✉️ Contact</td>
      <td style="padding:4px 0;">[Email or "Not listed"]</td>
    </tr>
  </table>

  <a href="[link]" style="display:inline-block; margin-top:14px; background:#4a4a8a; color:white; padding:9px 20px; border-radius:6px; text-decoration:none; font-size:14px;">Apply Now →</a>

</div>

Start with this summary line before the cards:
<p style="font-size:15px; color:#444;">Found <strong>[X] matching roles</strong> out of [total] listings reviewed — [Date]. Sorted by work auth compatibility then match score.</p>

If zero jobs match after filtering, return:
<p style="color:#888;">No new matching listings found in this batch. Next run scheduled soon.</p>

## Job Listings to Analyze:
{jobs_text}
"""
    return prompt


def analyze_jobs_with_claude(all_jobs):
    """
    Splits jobs into batches by country context,
    sends each batch to Claude with the right filters,
    combines results into one email.
    """
    if not all_jobs:
        print("No jobs to analyze.")
        return "<p style='color:#888;'>No new job listings found today.</p>"

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # ── Group jobs by country context ──
    country_batches = {"usa": [], "india": [], "singapore": [], "ireland": []}
    for job in all_jobs:
        ctx = detect_country_context(job.get("location", ""))
        country_batches[ctx].append(job)

    all_html_sections = []

    country_labels = {
        "usa":       "🇺🇸 United States",
        "india":     "🇮🇳 India",
        "singapore": "🇸🇬 Singapore",
        "ireland":   "🇮🇪 Ireland",
    }

    for country, jobs in country_batches.items():
        if not jobs:
            continue

        # Skip if country not active
        if not ACTIVE_COUNTRIES.get(country, False):
            continue

        print(f"\n🤖 Analyzing {len(jobs)} jobs for {country_labels[country]}...")

        # Batch into chunks of 30 (token limit safety)
        batch_size = 30
        country_html_parts = []

        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(jobs) + batch_size - 1) // batch_size
            print(f"  📦 Batch {batch_num}/{total_batches} — {len(batch)} jobs")

            try:
                prompt = build_claude_prompt(batch, country)
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                country_html_parts.append(response.content[0].text)
                time.sleep(1)  # Avoid rate limiting

            except Exception as e:
                print(f"  ❌ Claude error on batch {batch_num}: {e}")
                country_html_parts.append(
                    f"<p style='color:red;'>Error analyzing batch {batch_num}: {e}</p>"
                )

        # Wrap country section with header
        country_section = f"""
<div style="margin-bottom:40px;">
  <div style="background:#1a1a2e; color:white; padding:14px 20px; border-radius:8px; margin-bottom:20px;">
    <h2 style="margin:0; font-size:18px;">{country_labels[country]}</h2>
    <p style="margin:4px 0 0 0; opacity:0.7; font-size:13px;">{len(jobs)} listings reviewed</p>
  </div>
  {''.join(country_html_parts)}
</div>
"""
        all_html_sections.append(country_section)
        print(f"  ✅ {country_labels[country]} analysis complete")

    if not all_html_sections:
        return "<p style='color:#888;'>No matching jobs found across any region today.</p>"

    print("\n✅ All Claude analysis complete")
    return "\n".join(all_html_sections)

# ──────────────────────────────────────────────
# STEP 3: Send the email digest to yourself
# ──────────────────────────────────────────────
def send_email(html_content):
    sender_email = os.environ["EMAIL_ADDRESS"]
    sender_password = os.environ["EMAIL_APP_PASSWORD"]
    recipient_email = os.environ["EMAIL_TO"]

    today = datetime.now().strftime("%B %d, %Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚀 Product Engineer Jobs — OPT/H1B Friendly | {today}"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    # Plain text fallback
    plain_text = "Your daily product engineer job digest is ready. Please view in an HTML-compatible email client."

    # Full HTML email with header and footer
    full_html = f"""
    <html>
    <body style="font-family:Arial,sans-serif; max-width:700px; margin:auto; padding:20px; background:#f9f9f9;">

      <div style="background:linear-gradient(135deg,#1a1a2e,#4a4a8a); color:white; padding:24px; border-radius:10px; margin-bottom:24px;">
        <h1 style="margin:0; font-size:22px;">🚀 Daily Job Digest</h1>
        <p style="margin:8px 0 0 0; opacity:0.85;">Product Engineer Roles — OPT/H1B Friendly | {today}</p>
      </div>

      <div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:12px; margin-bottom:24px;">
        <strong>⚠️ OPT Tip:</strong> Always verify sponsorship directly with the recruiter.
        Check <a href="https://www.myvisajobs.com">myvisajobs.com</a> to confirm a company's H1B history before applying.
      </div>

      {html_content}

      <div style="text-align:center; color:#999; font-size:12px; margin-top:32px; padding-top:16px; border-top:1px solid #eee;">
        <p>This digest was generated automatically using Claude AI + GitHub Actions.<br>
        Ran on: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}</p>
      </div>

    </body>
    </html>
    """

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(full_html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"✅ Email sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        raise


# ──────────────────────────────────────────────
# MAIN — runs the full pipeline
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"  Job Search Bot Starting — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # 1. Fetch jobs
    jobs = fetch_jobs_from_indeed()

    # 2. Analyze with Claude
    analysis_html = analyze_jobs_with_claude(jobs)

    # 3. Email results
    send_email(analysis_html)

    print("\n✅ Job search pipeline complete!\n")











