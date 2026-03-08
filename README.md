# 🤖 Job Search Automation Bot

I got tired of manually checking LinkedIn, Indeed, and Naukri every day across multiple countries. So I built this.

Every morning at 8 AM — in the country's timezone, so you can apply at 8am in the country's time as soon as the jobs release — this bot wakes up, scrapes fresh job postings, matches them against your resume using AI, and sends you the top 10 most relevant jobs straight to your inbox. No dashboards, no logins, no manual work. Just open your email and apply.

It runs entirely on **GitHub Actions** and uses **only free tools**. Zero cost.

---

## 📬 What Lands in Your Inbox

```
Subject: 🧑‍💻 Top 10 Job Matches — USA | March 06, 2026

#1  Senior Electrical Engineer @ Siemens          91% match
    📍 Remote, USA  |  🔗 LinkedIn  |  📅 Today
    ✅ MATLAB  ✅ Circuit Design  ✅ Python  ❌ VHDL
    [View Job →]

#2  Testing Engineer @ Texas Instruments          87% match
    📍 Austin, TX  |  🔗 Indeed
    ✅ Testing  ✅ Embedded Systems  ❌ LabVIEW
    [View Job →]
```

You get 3 emails a day — one for USA (8 AM CST), one for India (8 AM IST), one for Singapore (8 AM SST).

---

## 🚀 Use This Yourself — 4 Steps

You don't need to understand the code. Just follow these steps and you'll have job alerts running in under 15 minutes.


---

### Step 1 — Fork This Repo

Click the **Fork** button at the top right of this page. This creates your own private copy of the bot under your GitHub account. You need to have a GitHub Account.

---

### Step 2 — Add Your Resume

Delete the existing resume file in the `resumes/` folder and upload your own `.docx` resume there.

Then open `src/resume_parser.py` and update **line 11** with your filename:

```python
# Change this to match your resume filename exactly
RESUME_PATH = os.path.join(
    os.path.dirname(__file__), '..', 
    'resumes', 'YOUR_RESUME_FILENAME.docx'   # ← change this
)
```

That's the only line of code you need to touch.

---

### Step 3 — Add Your Secrets

Go to your forked repo on GitHub:

```
Settings → Secrets and variables → Actions → New repository secret
```

Add these 4 secrets one by one:

| Secret Name | What to put in it |
|-------------|-------------------|
| `GROQ_API_KEY` | Get a free key at [console.groq.com](https://console.groq.com) → no credit card needed |
| `EMAIL_ADDRESS` | Your Sending Gmail address e.g. `yourname@gmail.com` This can be a same email address as your receiving address|
| `EMAIL_APP_PASSWORD` | A Gmail App Password — see instructions below ↓ |
| `EMAIL_TO` | The email address where you want to receive job alerts |

#### How to get a Gmail App Password
```
1. Go to → myaccount.google.com/security
2. Make sure 2-Step Verification is turned ON
3. Go to → myaccount.google.com/apppasswords
4. Type "JobBot" as the app name → click Create
5. Copy the 16-character password shown
6. Paste it into EMAIL_APP_PASSWORD (remove all spaces)
```

> This is NOT your real Gmail password. It is a separate one-time password
> Google generates just for this bot.

---

### Step 4 — Parse Your Resume and Start

First, let the bot read your resume and extract your skills:

```
GitHub → Actions tab → "Step 2 — Parse Resume" → Run workflow
```

Wait for it to finish (about 30 seconds). It will automatically save a `resume_profile.json` file to your repo — this is how the bot knows what jobs to match against you.
Note: if you are in career transition or want add more keywords or roles you can add them in the updated `resume_profile.json` as it automatically updates when you run `Step 2 - Parse Resume` 

Then do a test run to confirm you receive an email:

```
GitHub → Actions tab → "USA Jobs — Daily 8AM CST" → Run workflow
```

Check your inbox. If the email arrives, you're done. The bot will now run automatically every day.

---

## 🌍 Which Countries Are Supported

| Country | Email Time | Boards Searched |
|---------|-----------|-----------------|
| 🇺🇸 USA | 8:00 AM CST | Indeed + LinkedIn |
| 🇮🇳 India | 8:00 AM IST | Indeed + LinkedIn + Naukri |
| 🇸🇬 Singapore | 8:00 AM SST | Indeed + LinkedIn |

Want to add another country? See the section at the bottom of this README.

---

## 🧠 How It Works

You don't need to know this to use it — but here's what happens under the hood every morning:

```
1. GitHub Actions wakes up at the scheduled time
2. Loads your resume profile (skills, titles, seniority)
3. Scrapes Indeed + LinkedIn for jobs posted in the last 24 hours
4. Runs TF-IDF cosine similarity to filter the best 20 candidates
5. Sends top 20 to Groq AI (free) for intelligent re-ranking
6. Emails you the final top 10 with match scores and skill breakdowns
```

The entire run takes about 2-3 minutes and costs $0.

---

## 💰 Cost Breakdown

Everything used here has a free tier that comfortably covers daily usage:

| Tool | What it does | Free limit | Daily use |
|------|-------------|------------|-----------|
| GitHub Actions | Runs the bot on a schedule | 2,000 min/month | ~15 min/day |
| JobSpy | Scrapes Indeed + LinkedIn | Unlimited | ~6 calls/day |
| Groq (Llama 3.1) | AI resume matching | 14,400 req/day | 3 req/day |
| Gmail SMTP | Sends the email | 500 emails/day | 3 emails/day |

**Total: $0/month**

---

## ➕ Adding a New Country

Open `config/countries.yaml` and add a new entry following this pattern:

```yaml
- name: Australia
  timezone: Australia/Sydney
  cron_utc: "0 22 * * *"      # 8 AM AEDT = 22:00 UTC
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

Then create `.github/workflows/australia_jobs.yml` by copying any existing country workflow file and changing the last line to `--country Australia`.

That's it. The entire bot is driven by this config file — no other code changes needed.

---

## 🔧 Something Not Working?

| Symptom | What's happening | Fix |
|---------|-----------------|-----|
| No email received | Secrets not set correctly | Double-check all 4 secrets are added with exact names |
| Email received but no jobs | Resume not parsed yet | Run the `parse_resume.yml` workflow first |
| `EMAIL_ADDRESS`,`EMAIL_APP_PASSWORD`, `EMAIL_TO` error | Special characters in password | Remove all spaces from the app password before saving |
| Low match scores | Job descriptions are short (normal) | Bot still picks the most relevant — scores improve when Groq re-ranks |
| Workflow didn't run at scheduled time | GitHub delays scheduled runs on free accounts | Trigger manually once — scheduled runs will normalize |

---

## 🗂️ File Structure Reference

```
├── .github/workflows/
│   ├── parse_resume.yml       # Run once to parse your resume
│   ├── usa_jobs.yml           # Runs daily 8 AM CST
│   ├── india_jobs.yml         # Runs daily 8 AM IST
│   └── singapore_jobs.yml     # Runs daily 8 AM SST
│
├── config/
│   └── countries.yaml         # Add or remove countries here
│
├── data/
│   └── resume_profile.json    # Auto-generated — do not edit
│
├── resumes/
│   └── your_resume.docx       # ← Replace with your resume
│
└── src/
    ├── main.py                # Runs the full pipeline
    ├── resume_parser.py       # ← Update your filename here (line 11)
    ├── scorer.py              # TF-IDF + Groq matching
    ├── email_sender.py        # Gmail digest builder
    └── scraper/
        └── jobspy_scraper.py  # Indeed + LinkedIn scraper
```

---

## 🔮 What I Plan to Add Next

- Deduplicate jobs across days so you don't see the same posting twice
- Remote-only filter toggle in the config
- Salary range filter
- Weekly digest summary option
  

---

Built this for myself with AI assistance from Claude, sharing it because it genuinely saves time every day. If you use it and something breaks or you want a feature — open an issue.
