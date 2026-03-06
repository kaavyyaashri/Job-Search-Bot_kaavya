# 🤖 Job Search Automation Bot

Automatically scrapes jobs from **Indeed + LinkedIn** across **USA, India, and Singapore**, matches them against your resume using AI, and emails you the **top 10 matches daily** — all for free using GitHub Actions.

---

## 📬 What You Get Every Morning

Three emails land in your inbox daily — one per country — each timed to 8 AM local time:

```
Subject: 🧑‍💻 Top 10 Job Matches — USA | March 06, 2026

#1  Senior Electrical Engineer @ Siemens     91% match
    📍 Remote, USA  |  🔗 LinkedIn  |  📅 Mar 06, 2026
    ✅ Python  ✅ MATLAB  ✅ Circuit Design  ❌ VHDL
    [View Job →]

#2  Testing Engineer @ Texas Instruments     87% match
    ...
```

---

## 🏗️ Architecture

```
GitHub Actions (cron schedule)
        ↓
  main.py --country USA
        ↓
┌─────────────────────────────────────┐
│  1. Load resume_profile.json        │  ← parsed from your .docx
│  2. JobSpy scrapes Indeed+LinkedIn  │  ← ~50-100 raw jobs
│  3. TF-IDF filters → top 20         │  ← scikit-learn, zero API cost
│  4. Groq re-ranks → top 10          │  ← Llama 3.1 8B, free tier
│  5. Gmail SMTP sends email digest   │  ← HTML email with job cards
└─────────────────────────────────────┘
```

---

## 📁 Project Structure

```
job-search-automation/
├── .github/workflows/
│   ├── parse_resume.yml         # Manual: parses resume → saves profile JSON
│   ├── usa_jobs.yml             # Daily 8AM CST  (14:00 UTC)
│   ├── india_jobs.yml           # Daily 8AM IST  (02:30 UTC)
│   └── singapore_jobs.yml       # Daily 8AM SST  (00:00 UTC)
│
├── config/
│   └── countries.yaml           # ← Add new countries here only
│
├── data/
│   └── resume_profile.json      # Auto-generated — do not edit manually
│
├── resumes/
│   └── your_resume.docx         # Your resume file
│
├── src/
│   ├── main.py                  # Pipeline orchestrator
│   ├── config_loader.py         # Reads countries.yaml
│   ├── resume_parser.py         # Extracts profile from resume (Groq)
│   ├── scorer.py                # TF-IDF + Groq re-ranking
│   ├── email_sender.py          # Gmail SMTP digest sender
│   └── scraper/
│       ├── base_scraper.py      # Abstract base class + Job dataclass
│       └── jobspy_scraper.py    # Indeed + LinkedIn via JobSpy
│
└── requirements.txt
```

---

## ⚙️ Setup Guide

### Step 1 — Fork or Clone This Repo

```bash
git clone https://github.com/yourname/job-search-automation.git
cd job-search-automation
```

### Step 2 — Add Your Resume

Place your resume in the `resumes/` folder:
```
resumes/your_resume.docx
```

Update the path in `src/resume_parser.py`:
```python
RESUME_PATH = os.path.join(os.path.dirname(__file__), '..', 'resumes', 'your_resume.docx')
```

### Step 3 — Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value | Where to get it |
|-------------|-------|-----------------|
| `GROQ_API_KEY` | `gsk_...` | [console.groq.com](https://console.groq.com) → free |
| `EMAIL_ADDRESS` | `you@gmail.com` | Your Gmail address |
| `EMAIL_APP_PASSWORD` | 16-char password | [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) |
| `EMAIL_TO` | `you@gmail.com` | Where to receive job alerts |

> ⚠️ Use a **Gmail App Password**, not your real Gmail password. Go to Google Account → Security → 2-Step Verification → App Passwords.

### Step 4 — Parse Your Resume

```
GitHub → Actions → "Step 2 — Parse Resume" → Run workflow
```

This reads your `.docx`, extracts your skills and target titles using Groq, and saves `data/resume_profile.json` to the repo automatically.

### Step 5 — Run Manually to Test

```
GitHub → Actions → "USA Jobs — Daily 8AM CST" → Run workflow
```

Check your inbox — you should receive a job digest email within 2 minutes.

---

## 🌍 Adding a New Country

Only one file to edit — `config/countries.yaml`:

```yaml
- name: Australia
  timezone: Australia/Sydney
  cron_utc: "0 22 * * *"        # 8 AM AEDT = 22:00 UTC
  send_email_at: "08:00"
  boards:
    - indeed
    - linkedin
  search_keywords:
    - "software engineer"
    - "backend developer"
  location_keywords:
    - "Sydney"
    - "Melbourne"
    - "Remote"
```

Then create `.github/workflows/australia_jobs.yml` using any existing country workflow as a template, changing `--country Australia`.

---

## 🔧 How It Works — Module by Module

### Resume Parser (`resume_parser.py`)
- Reads your `.docx` resume using `python-docx`
- Sends text to **Groq Llama 3.1 8B** with a structured JSON prompt
- Extracts: target titles, skills, seniority, industries, education
- Saves to `data/resume_profile.json`
- Runs **once** — re-run only when you update your resume

### Scraper (`scraper/jobspy_scraper.py`)
- Uses **JobSpy** to scrape Indeed + LinkedIn
- Searches using your resume's target titles as keywords
- Filters to jobs posted in the **last 24 hours**
- Returns ~50-100 raw Job objects per country

### Scorer (`scorer.py`)

**Stage 1 — TF-IDF (free, instant):**
- Converts resume profile + all job descriptions to TF-IDF vectors
- Computes cosine similarity between resume and each job
- Filters down to top 20 candidates

**Stage 2 — Groq re-ranking (1 API call/day):**
- Sends top 20 jobs + resume profile to Groq Llama 3.1 8B
- Gets back: rank, match score (0-100%), match reason, matched skills, missing skills
- Falls back to TF-IDF scores if Groq fails

### Email Sender (`email_sender.py`)
- Builds a clean HTML email with job cards
- Sends via **Gmail SMTP** (port 465, SSL)
- Each card shows: title, company, location, match %, skills breakdown, direct link

---

## 📊 Free Tier Usage

| Service | Used For | Free Limit | Daily Usage |
|---------|----------|------------|-------------|
| **Groq** | Resume parsing + re-ranking | 14,400 req/day | 3 req/day |
| **JobSpy** | Scraping Indeed + LinkedIn | Unlimited | ~6 calls/day |
| **Gmail SMTP** | Sending emails | 500 emails/day | 3 emails/day |
| **GitHub Actions** | Running everything | 2,000 min/month | ~15 min/day |

**Total cost: $0/month** ✅

---

## 🛠️ Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| No jobs scraped | JobSpy blocked or slow | Re-run workflow, it's usually transient |
| Groq re-ranking failed | JSON parse error from special characters | Falls back to TF-IDF automatically |
| Email not received | App password has spaces/special chars | Remove all spaces from app password secret |
| `resume_profile.json` not found | Resume not parsed yet | Run `parse_resume.yml` workflow first |
| Low match scores (< 20%) | Short job descriptions, TF-IDF limitation | Groq re-ranking gives better scores |
| 403 on job boards | Datacenter IP block | JobSpy handles this — if persistent, wait 1 hour |

---

## 🔮 Future Improvements

- [ ] Deduplicate jobs across days (avoid seeing same job twice)  
- [ ] Filter out already-applied jobs  
- [ ] Add more countries (Australia, UK, Canada)  
- [ ] Slack/WhatsApp notification option  
- [ ] Weekly summary digest  
- [ ] Salary range filter  
- [ ] Remote-only filter toggle in config  

---

## 📦 Dependencies

```
python-jobspy       # Job scraping (Indeed, LinkedIn)
groq                # LLM for resume parsing + re-ranking
scikit-learn        # TF-IDF cosine similarity scoring
numpy               # Numerical operations
python-docx         # Reading .docx resume
pyyaml              # Reading countries.yaml config
python-dateutil     # Date parsing from job listings
pytz                # Timezone handling
jinja2              # HTML email templating
```

Install locally:
```bash
pip install -r requirements.txt
```

---

## 🧪 Testing Workflows

| Workflow | Purpose |
|----------|---------|
| `parse_resume.yml` | Parse resume → generate profile JSON |
| `test_step3.yml` | Test scraper for a specific country |
| `test_step4.yml` | Test scraper + scorer together |
| `test_step5.yml` | Test email sending with dummy jobs |

---

## License

MIT — use freely, modify as needed.
