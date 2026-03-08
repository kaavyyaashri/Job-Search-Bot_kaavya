import os
import json
from datetime import datetime, timezone
from .base_scraper import BaseScraper, Job

INDEED_COUNTRY_MAP = {
    "USA":       "USA",
    "India":     "India",
    "Singapore": "Singapore",
}

RESUME_PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'data', 'resume_profile.json'
)

def load_resume_titles() -> list[str]:
    """Load target job titles from parsed resume profile"""
    try:
        with open(RESUME_PROFILE_PATH, 'r') as f:
            profile = json.load(f)
        titles = profile.get('target_titles', [])
        print(f"   📄 Resume titles loaded: {titles}")
        top_2 = titles[:2] 
        return top_2       # top 2 titles to keep calls efficient
    except Exception as e:
        print(f"   ⚠️  Could not load resume profile: {e}")
        return ["software engineer"] # safe fallback

class JobSpyScraper(BaseScraper):

    def scrape(self) -> list[Job]:
        try:
            from jobspy import scrape_jobs
        except ImportError:
            print("   ⚠️  jobspy not installed. Run: pip install python-jobspy")
            return []

        # ── Use resume titles as search terms, not countries.yaml keywords ──
        search_terms = load_resume_titles()

        all_jobs = []
        for term in search_terms:
            jobs = self._fetch_jobs(scrape_jobs, term)
            all_jobs.extend(jobs)

        # Deduplicate by URL
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique_jobs.append(job)

        print(f"   JobSpy → {len(unique_jobs)} unique jobs found for {self.country}")
        return unique_jobs

def _fetch_jobs(self, scrape_jobs, search_term: str) -> list[Job]:
    country_name   = self.country
    indeed_country = INDEED_COUNTRY_MAP.get(country_name, "USA")
    location       = self.locations[0] if self.locations else country_name

    board_map = {
        "indeed":    "indeed",
        "linkedin":  "linkedin",
        "glassdoor": "glassdoor",
    }
    site_names = [board_map[b] for b in self.country_config.get('boards', ['indeed']) if b in board_map]

    if not site_names:
        print(f"   ⚠️  No supported boards configured for {country_name}")
        return []

    try:
        print(f"   🔎 Searching '{search_term}' on {site_names} in {location}...")

        df = scrape_jobs(
            site_name=site_names,
            search_term=search_term,
            location=location,
            results_wanted=25,
            hours_old=24,
            country_indeed=indeed_country,
            verbose=0,
        )

        if df is None or df.empty:
            print(f"   ⚠️  No results for '{search_term}' in {location}")
            return []

        # ── Debug listing_type — OUTSIDE the row loop ──────
        print(f"   📋 listing_type unique values: {df['listing_type'].dropna().unique().tolist()}")
        print(f"   📋 Easy apply count: {df['listing_type'].str.contains('easy', case=False, na=False).sum()}")

        jobs = []
        for _, row in df.iterrows():
            try:
                # Normalize posted date
                raw_date = row.get('date_posted')
                if raw_date and str(raw_date) != 'nan':
                    try:
                        posted_at = raw_date.isoformat() if hasattr(raw_date, 'isoformat') else str(raw_date)
                    except Exception:
                        posted_at = datetime.now(timezone.utc).isoformat()
                else:
                    posted_at = datetime.now(timezone.utc).isoformat()

                title        = str(row.get('title',        '') or '').strip()
                company      = str(row.get('company',      '') or 'Unknown').strip()
                loc_str      = str(row.get('location',     '') or location).strip()
                desc         = str(row.get('description',  '') or '')[:500]
                url          = str(row.get('job_url',      '') or '').strip()
                source       = str(row.get('site',         '') or 'unknown').strip()
                listing_type = str(row.get('listing_type', '') or '').lower()
                easy_apply   = 'easy_apply' in listing_type or 'easy apply' in listing_type

                if easy_apply:
                    print(f"   🚫 Easy Apply detected: {title} @ {company} | listing_type='{listing_type}'")

                if not title or not url or url == 'nan':
                    continue

                jobs.append(Job(
                    title=title,
                    company=company,
                    location=loc_str,
                    posted_at=posted_at,
                    description=desc,
                    url=url,
                    source=source,
                    country=self.country,
                    easy_apply=easy_apply
                ))

            except Exception as e:
                continue

        return jobs

    except Exception as e:
        print(f"   ⚠️  JobSpy error for '{search_term}' in {location}: {e}")
        return []
