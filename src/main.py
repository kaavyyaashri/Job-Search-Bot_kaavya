import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from config_loader import get_country_config
from scraper import get_scraper
from job_filter import filter_jobs
from scorer import score_and_rank
from job_filter import filter_jobs #, filter_by_applicants 
from email_sender import send_email

RESUME_PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'resume_profile.json'
)

def load_resume_profile() -> dict:
    with open(RESUME_PROFILE_PATH, 'r') as f:
        return json.load(f)

def run_pipeline(country_name: str):
    print(f"\n{'='*60}")
    print(f"  🤖 Job Search Pipeline — {country_name}")
    print(f"{'='*60}\n")

    # ── Step 1: Load config ────────────────────────────────
    print("📋 Step 1 — Loading config...")
    config = get_country_config(country_name)
    print(f"   ✅ Country  : {config['name']}")
    print(f"   ✅ Boards   : {config['boards']}")
    print(f"   ✅ Timezone : {config['timezone']}\n")

    # ── Step 2: Load resume profile ───────────────────────
    print("📄 Step 2 — Loading resume profile...")
    try:
        resume = load_resume_profile()
        print(f"   ✅ Titles   : {resume.get('target_titles')}")
        print(f"   ✅ Skills   : {len(resume.get('skills', []))} skills loaded")
        print(f"   ✅ Seniority: {resume.get('seniority')}\n")
    except FileNotFoundError:
        print("   ❌ resume_profile.json not found!")
        print("   Run the parse_resume workflow first.")
        sys.exit(1)

    # ── Step 3: Scrape jobs ───────────────────────────────
    print("🔍 Step 3 — Scraping jobs...")
    scrapers  = get_scraper(ocuntry_config, country_name)
    all_jobs  = []
    
    for scraper in scrapers:
        jobs = scraper.scrape()
        all_jobs.extend(jobs)
    
    # Deduplicate across scrapers by URL
    seen       = set()
    unique     = []
    for job in all_jobs:
        url = job.url if hasattr(job, 'url') else job.get('url', '')
        if url not in seen:
            seen.add(url)
            unique.append(job)

    print(f"   ✅ Total jobs scraped: {len(unique)}")
    # print("🔍 Step 3 — Scraping jobs...")
    # scraper    = JobSpyScraper(config)
    # jobs       = scraper.scrape()

    # if not jobs:
    #     print(f"\n⚠️  No jobs scraped for {country_name} — skipping.")
    #     sys.exit(0)

    # jobs_dicts = [vars(j) for j in jobs]
    # print(f"   ✅ Total jobs scraped: {len(jobs_dicts)}\n")
    

    # ── Step 4: Filter ineligible jobs ───────────────────  ← NEW
    print("🚫 Step 4 — Filtering ineligible jobs...")
    eligible, excluded = filter_jobs(jobs_dicts)

    print(f"   ✅ Eligible jobs : {len(eligible)}")
    print(f"   🚫 Excluded jobs : {len(excluded)}")

    if excluded:
        print(f"\n   Excluded because of:")
        from collections import Counter
        reasons = Counter(j['excluded_reason'] for j in excluded)
        for reason, count in reasons.most_common():
            print(f"      '{reason}' → {count} jobs removed")

    if not eligible:
        print(f"\n⚠️  All jobs were filtered out — skipping email.")
        sys.exit(0)

    print()
    
    # ── Step 5: Score and rank ─────────────────────────────
    print("🧠 Step 5 — Scoring and ranking jobs...")
    top_jobs = score_and_rank(eligible)
    
    if not top_jobs:
        print(f"\n⚠️  Scoring returned no results — skipping email.")
        sys.exit(0)
    
    print(f"\n   🏆 Top {len(top_jobs)} jobs selected:\n")
    for job in top_jobs:
        print(
            f"   #{job.get('rank', '?'):>2}  {job.get('match_score', 0):>3}%  "
            f"{job['title'][:40]:<40}  {job['company'][:25]}"
        )
    
    # # ── Step 5b: Filter by applicant count ────────────────  ← NEW
    # print("\n👥 Step 5b — Checking applicant counts...")
    # top_jobs = filter_by_applicants(top_jobs, max_applicants=20)
    
    # if not top_jobs:
    #     print(f"\n⚠️  All jobs had too many applicants — skipping email.")
    #     sys.exit(0)

    # ── Step 6: Send email ────────────────────────────────
    print(f"\n📧 Step 6 — Sending email...")
    send_email(top_jobs, country_name)

    print(f"\n{'='*60}")
    print(f"  ✅ Pipeline complete for {country_name}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Job Search Automation')
    parser.add_argument('--country', required=True, help='USA / India / Singapore')
    args = parser.parse_args()
    run_pipeline(args.country)
