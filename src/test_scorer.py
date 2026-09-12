import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from config_loader import get_country_config
from scraper.jobspy_scraper import JobSpyScraper
from scorer import score_and_rank

def test_scoring(country_name: str):
    print(f"\n🧪 Testing Full Scrape + Score Pipeline — {country_name}")
    print("=" * 60)

    # Step 1 — Scrape
    config  = get_country_config(country_name)
    scraper = JobSpyScraper(config)
    jobs    = scraper.scrape()

    if not jobs:
        print("⚠️  No jobs scraped — cannot test scorer")
        return

    # Convert Job dataclass to dict for scorer
    jobs_dicts = [vars(j) for j in jobs]
    print(f"\n✅ Scraped {len(jobs_dicts)} jobs — starting scorer...\n")

    # Step 2 — Score
    top_10 = score_and_rank(jobs_dicts)

    # Step 3 — Print results
    print("\n" + "=" * 60)
    print(f"🏆 TOP {len(top_10)} JOBS FOR {country_name.upper()}")
    print("=" * 60)

    for job in top_10:
        print(f"\n#{job.get('rank', '?')} — {job['title']} @ {job['company']}")
        print(f"   📍 Location     : {job['location']}")
        print(f"   🎯 Match Score  : {job.get('match_score', 'N/A')}%")
        print(f"   💡 Reason       : {job.get('match_reason', 'N/A')}")
        print(f"   ✅ Matched      : {job.get('matched_skills', [])}")
        print(f"   ❌ Missing      : {job.get('missing_skills', [])}")
        print(f"   🔗 Source       : {job['source']}")
        print(f"   🔗 URL          : {job['url']}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--country', required=True)
    args = parser.parse_args()
    test_scoring(args.country)
