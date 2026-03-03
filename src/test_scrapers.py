import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config_loader import get_country_config
from scraper.linkedin_scraper import LinkedInScraper

def test_linkedin(country_name: str):
    print(f"\n🔍 Testing LinkedIn Scraper — {country_name}")
    print("=" * 50)

    config  = get_country_config(country_name)
    scraper = LinkedInScraper(config)
    jobs    = scraper.scrape()

    print(f"\n✅ Total jobs scraped: {len(jobs)}")

    if jobs:
        print(f"\n📋 Sample job #1:")
        print(f"   Title   : {jobs[0].title}")
        print(f"   Company : {jobs[0].company}")
        print(f"   Location: {jobs[0].location}")
        print(f"   Posted  : {jobs[0].posted_at}")
        print(f"   Source  : {jobs[0].source}")
        print(f"   URL     : {jobs[0].url[:80]}...")
    else:
        print("\n⚠️  No jobs returned — LinkedIn may be blocking RSS for this region.")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--country', required=True, help='USA / India / Singapore')
    args = parser.parse_args()

    test_linkedin(args.country)
