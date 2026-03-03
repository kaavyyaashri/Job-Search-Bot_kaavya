import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config_loader import get_country_config
from scraper.indeed_scraper import IndeedScraper
from scraper.glassdoor_scraper import GlassdoorScraper
from scraper.naukri_scraper import NaukriScraper

def print_sample(jobs, source):
    print(f"\n✅ {source} → {len(jobs)} jobs found")
    if jobs:
        print(f"   📋 Sample:")
        print(f"      Title   : {jobs[0].title}")
        print(f"      Company : {jobs[0].company}")
        print(f"      Location: {jobs[0].location}")
        print(f"      Posted  : {jobs[0].posted_at}")
        print(f"      URL     : {jobs[0].url[:80]}...")
    else:
        print(f"   ⚠️  No jobs returned")

def test_all(country_name: str):
    print(f"\n🔍 Testing All Scrapers — {country_name}")
    print("=" * 50)

    config  = get_country_config(country_name)
    boards  = config['boards']

    if 'indeed' in boards:
        jobs = IndeedScraper(config).scrape()
        print_sample(jobs, 'Indeed')

    if 'glassdoor' in boards:
        jobs = GlassdoorScraper(config).scrape()
        print_sample(jobs, 'Glassdoor')

    if 'naukri' in boards:
        jobs = NaukriScraper(config).scrape()
        print_sample(jobs, 'Naukri')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--country', required=True)
    args = parser.parse_args()
    test_all(args.country)
