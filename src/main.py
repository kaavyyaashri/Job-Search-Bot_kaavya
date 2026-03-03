import argparse
import json
import os
from config_loader import get_country_config

RESUME_PROFILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'resume_profile.json')

def load_resume_profile() -> dict:
    with open(RESUME_PROFILE_PATH, 'r') as f:
        return json.load(f)

def run_pipeline(country_name: str):
    print(f"\n{'='*50}")
    print(f"  Job Search Pipeline — {country_name}")
    print(f"{'='*50}\n")

    # Step 1: Load config
    config = get_country_config(country_name)
    print(f"✅ Config loaded for {country_name}")
    print(f"   Boards : {config['boards']}")
    print(f"   Timezone: {config['timezone']}\n")

    # Step 2: Load resume profile
    resume = load_resume_profile()
    print(f"✅ Resume profile loaded")
    print(f"   Titles : {resume['target_titles']}")
    print(f"   Skills : {resume['skills']}\n")

    # --- Modules plug in here as we build them ---
    # jobs     = scrape(config)         # Step 3
    # scored   = score(jobs, resume)    # Step 6
    # send_email(scored, country_name)  # Step 7

    print("🚧 Scraper, scorer, and email modules coming in next steps.\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Job Search Automation')
    parser.add_argument('--country', required=True, help='Country name e.g. USA, India, Singapore')
    args = parser.parse_args()
    run_pipeline(args.country)
