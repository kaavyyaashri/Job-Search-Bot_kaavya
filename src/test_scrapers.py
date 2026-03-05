import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config_loader import get_country_config
from scraper.jsearch_scraper import JSearchScraper

def print_sample(jobs, source):
    print(f"\n✅ {source} → {len(jobs)} jobs found")
    if jobs:
        print(f"\n📋 Sample jobs:")
        for i, job in enumerate(jobs[:3], 1):        # show first 3
            print(f"\n   #{i}")
            print(f"      Title   : {job.title}")
            print(f"      Company : {job.company}")
            print(f"      Location: {job.location}")
            print(f"      Source  : {job.source}")
            print(f"      Posted  : {job.posted_at}")
            print(f"      URL     : {job.url[:80]}...")
    else:
        print(f"   ⚠️  No jobs returned")

def test_all(country_name: str):
    print(f"\n🔍 Testing JSearch Scraper — {country_name}")
    print("=" * 50)

    config  = get_country_config(country_name)
    scraper = JSearchScraper(config)
    jobs    = scraper.scrape()

    print_sample(jobs, 'JSearch')

    print(f"\n📊 Sources breakdown:")
    from collections import Counter
    sources = Counter(j.source for j in jobs)
    for src, count in sources.items():
        print(f"   {src:15} : {count} jobs")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--country', required=True)
    args = parser.parse_args()
    test_all(args.country)
