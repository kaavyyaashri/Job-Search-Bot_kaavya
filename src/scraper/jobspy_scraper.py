import os
import sys
from datetime import datetime, timezone
from .base_scraper import BaseScraper, Job

# Country → Indeed country code mapping
INDEED_COUNTRY_MAP = {
    "USA":       "USA",
    "India":     "India",
    "Singapore": "Singapore",
}

# Country → Glassdoor location string
GLASSDOOR_LOCATION_MAP = {
    "USA":       "United States",
    "India":     "India",
    "Singapore": "Singapore",
}

class JobSpyScraper(BaseScraper):

    def scrape(self) -> list[Job]:
        try:
            from jobspy import scrape_jobs
        except ImportError:
            print("   ⚠️  jobspy not installed. Run: pip install python-jobspy")
            return []

        all_jobs = []

        for keyword in self.keywords[:2]:           # top 2 keywords from resume
            jobs = self._fetch_jobs(scrape_jobs, keyword)
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

    def _fetch_jobs(self, scrape_jobs, keyword: str) -> list[Job]:
        country_name   = self.country
        indeed_country = INDEED_COUNTRY_MAP.get(country_name, "USA")
        location       = GLASSDOOR_LOCATION_MAP.get(country_name, country_name)

        # Decide which boards to use per country config
        boards = self.country_config.get('boards', ['indeed'])

        # JobSpy board name mapping
        board_map = {
            "indeed":    "indeed",
            "glassdoor": "glassdoor",
            "naukri":    "naukri",
        }
        site_names = [board_map[b] for b in boards if b in board_map]

        if not site_names:
            print(f"   ⚠️  No supported boards configured for {country_name}")
            return []

        try:
            print(f"   Searching '{keyword}' on {site_names} in {location}...")

            df = scrape_jobs(
                site_name=site_names,
                search_term=keyword,
                location=location,
                results_wanted=25,          # fetch 25, scorer picks top 10
                hours_old=24,               # last 24 hours only
                country_indeed=indeed_country,
                verbose=0,                  # suppress jobspy internal logs
            )

            if df is None or df.empty:
                print(f"   ⚠️  No results returned for '{keyword}' in {location}")
                return []

            jobs = []
            for _, row in df.iterrows():
                try:
                    # Normalize date
                    raw_date = row.get('date_posted')
                    if raw_date and str(raw_date) != 'nan':
                        try:
                            if hasattr(raw_date, 'isoformat'):
                                posted_at = raw_date.isoformat()
                            else:
                                from dateutil import parser as dp
                                posted_at = dp.parse(str(raw_date)).isoformat()
                        except Exception:
                            posted_at = datetime.now(timezone.utc).isoformat()
                    else:
                        posted_at = datetime.now(timezone.utc).isoformat()

                    # Build location string
                    city    = str(row.get('location', '') or '')
                    loc_str = city if city and city != 'nan' else location

                    # Description — combine title + description for scoring
                    desc = str(row.get('description', '') or '')[:500]

                    title   = str(row.get('title', '')   or '').strip()
                    company = str(row.get('company', '') or 'Unknown').strip()
                    url     = str(row.get('job_url', '')  or '').strip()
                    source  = str(row.get('site', '')     or 'unknown').strip()

                    # Skip rows with missing essentials
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
                        country=self.country
                    ))

                except Exception as e:
                    print(f"   ⚠️  Skipping row due to error: {e}")
                    continue

            return jobs

        except Exception as e:
            print(f"   ⚠️  JobSpy error for '{keyword}' in {location}: {e}")
            return []
