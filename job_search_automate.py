# Job Search automate code with the help of Claude

import anthropic
import smtplib
import requests
import os
import xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ─────────────────────────────────────────────
# YOUR PROFILE — Edit this section
# ──────────────────────────────────────────────
YOUR_PROFILE = """
Role: Product Engineer
Skills: React, Node.js, Python, API design, system design, cross-functional collaboration
Education: Masters degree (Computer Science or related field)
Work Authorization: OPT/CPT — actively requires H1B sponsorship
Experience Level: New grad / Entry level / 0-2 years
Preferred Company Size: Startups, mid-size tech, or large tech companies known for sponsoring
Preferred Location: Remote, or major US tech hubs (SF, NYC, Seattle, Austin, Boston)
"""

# ──────────────────────────────────────────────
# JOB SEARCH QUERIES — Edit roles/locations here
# ──────────────────────────────────────────────
SEARCH_QUERIES = [
    {"q": "product engineer", "l": "United States"},
    {"q": "product engineer visa sponsorship", "l": "United States"},
    {"q": "product engineer new grad masters", "l": "United States"},
    {"q": "product engineer OPT sponsor", "l": "United States"},
    {"q": "software engineer product h1b sponsor", "l": "United States"},
]

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
# STEP 1: Fetch jobs from Indeed RSS feeds
# ──────────────────────────────────────────────
def fetch_jobs_from_indeed():
    all_jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for query in SEARCH_QUERIES:
        url = (
            f"https://www.indeed.com/rss"
            f"?q={requests.utils.quote(query['q'])}"
            f"&l={requests.utils.quote(query['l'])}"
            f"&sort=date"
            f"&fromage=1"  # Jobs posted in last 1 day
        )
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall(".//item")
                for item in items:
                    title = item.findtext("title", "").strip()
                    link = item.findtext("link", "").strip()
                    description = item.findtext("description", "").strip()
                    pub_date = item.findtext("pubDate", "").strip()
                    source = item.findtext("source", "Indeed").strip()

                    all_jobs.append({
                        "title": title,
                        "link": link,
                        "description": description[:800],  # trim for token limits
                        "date": pub_date,
                        "source": source or "Indeed",
                    })
            else:
                print(f"Indeed RSS returned {response.status_code} for: {query['q']}")
        except Exception as e:
            print(f"Error fetching jobs for '{query['q']}': {e}")

    # Deduplicate by link
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        if job["link"] not in seen:
            seen.add(job["link"])
            unique_jobs.append(job)

    print(f"✅ Fetched {len(unique_jobs)} unique job listings from Indeed")
    return unique_jobs


# ──────────────────────────────────────────────
# STEP 2: Filter and enrich jobs using Claude
# ──────────────────────────────────────────────
def analyze_jobs_with_claude(jobs):
    if not jobs:
        print("No jobs to analyze.")
        return "<p>No new job listings found today.</p>"

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Format jobs into a readable block for Claude
    jobs_text = ""
    for i, job in enumerate(jobs[:40], 1):  # Limit to 40 to manage tokens
        jobs_text += f"""
---
Job #{i}
Title: {job['title']}
Link: {job['link']}
Posted: {job['date']}
Description: {job['description']}
---
"""

    known_sponsors_str = ", ".join(KNOWN_SPONSORS)

    prompt = f"""
You are a highly skilled job search assistant helping an international student on OPT/CPT
find Product Engineering roles in the US that offer H1B visa sponsorship.

## Candidate Profile:
{YOUR_PROFILE}

## Known H1B Sponsor Companies (prioritize these):
{known_sponsors_str}

## Your Task:
Review the following {len(jobs)} job listings and do the following:

### STEP 1 — FILTER
Only keep jobs that meet ALL of these criteria:
- Role is relevant to "Product Engineer" (includes software engineer with product focus, full-stack, platform engineer, etc.)
- Does NOT explicitly say "no sponsorship" or "must be authorized without sponsorship"
- Preferably open to new grads, Masters graduates, or entry-level candidates
- Based in the United States (remote is fine)

### STEP 2 — ENRICH each match with:
1. **Job Title** and **Company Name**
2. **Team / Department** hiring (if mentioned)
3. **Top 3 Requirements** from the listing
4. **Why It Matches** this candidate's profile (2 sentences)
5. **Company Overview** — what the company does, approximate size, notable products
6. **Sponsorship Likelihood** — one of: ✅ High (known sponsor or explicitly stated) / ⚠️ Medium (startup, no mention either way) / ❌ Low (signals against sponsorship)
7. **Application Link**
8. **Recruiter/Contact Email** — if mentioned in the listing (write "Not listed" if not found)

### STEP 3 — SORT results with ✅ High sponsorship likelihood first

### OUTPUT FORMAT:
Return a single clean HTML document (no markdown, no code blocks) ready to be sent as an email.
Use this structure for each job:

<div style="border:1px solid #e0e0e0; border-radius:8px; padding:16px; margin-bottom:20px; font-family:Arial,sans-serif;">
  <h2 style="color:#1a1a2e; margin:0 0 4px 0;">[Job Title]</h2>
  <h3 style="color:#4a4a8a; margin:0 0 12px 0;">[Company Name] — [Sponsorship Badge]</h3>
  <p><strong>Team:</strong> [Team/Department]</p>
  <p><strong>Top Requirements:</strong> [req1], [req2], [req3]</p>
  <p><strong>Why It Matches You:</strong> [2 sentences]</p>
  <p><strong>Company Overview:</strong> [2-3 sentences]</p>
  <p><strong>Contact Email:</strong> [email or "Not listed"]</p>
  <a href="[link]" style="background:#4a4a8a;color:white;padding:8px 16px;border-radius:4px;text-decoration:none;display:inline-block;margin-top:8px;">Apply Now →</a>
</div>

Start with a short summary line like: "Found X matching roles for today, [Date]."
If fewer than 3 jobs match, say so and list whatever matches exist.

## Job Listings to Analyze:
{jobs_text}
"""

    print("🤖 Sending jobs to Claude for analysis...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.content[0].text
    print("✅ Claude analysis complete")
    return result


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











