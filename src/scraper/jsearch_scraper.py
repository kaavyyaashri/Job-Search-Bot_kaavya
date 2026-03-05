import os
import requests
from datetime import datetime, timezone
from .base_scraper import BaseScraper, Job

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"

class JSearchScraper(BaseScraper):

    def scrape(self) -> list[Job]:
        api_key = os.environ.get('RAPIDAPI_KEY')
        if not api_key:
            raise ValueError("RAPIDAPI_KEY not set in environment/secrets")

        all_jobs = []

        # ── 1 call per country to stay within 100/month budget ──
        # Combine top keyword + location into one strong query
        keyword  = self.keywords[0]
        location = self.locations[0]
        query    = f"{keyword} in {location}"

        jobs = self._fetch_jobs(api_key, query)
        all_jobs.extend(jobs)

        # Deduplicate by URL
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique_jobs.append(job)

        print(f"   JSearch → {len(unique_jobs)} unique jobs found for {self.country}")
        return unique_jobs

    def _fetch_jobs(self, api_key: str, query: str) -> list[Job]:
        headers = {
            "X-RapidAPI-Key":  api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }

        params = {
            "query":            query,
            "page":             "1",
            "num_pages":        "1",        # 10 results per page
            "date_posted":      "today",    # only today's jobs
            "remote_jobs_only": "false",
        }

        try:
            response = requests.get(
                JSEARCH_URL,
                headers=headers,
                params=params,
                timeout=15
            )

            if response.status_code == 429:
                print(f"   ⚠️  JSearch rate limit hit — monthly quota may be exceeded")
                return []

            if response.status_code != 200:
                print(f"   ⚠️  JSearch error: {response.status_code} — {response.text[:200]}")
                return []

            data = response.json()
            jobs = []

            for item in data.get('data', []):
                # Parse posted date
                try:
                    timestamp  = item.get('job_posted_at_timestamp')
                    posted_at  = datetime.fromtimestamp(
                        int(timestamp), tz=timezone.utc
                    ).isoformat() if timestamp else datetime.now(timezone.utc).isoformat()
                except Exception:
                    posted_at = datetime.now(timezone.utc).isoformat()

                # Build job URL — prefer apply link, fallback to job page
                url = (
                    item.get('job_apply_link') or
                    item.get('job_google_link') or
                    ''
                )

                # Identify source board
                publisher = item.get('job_publisher', 'unknown').lower()
                if 'indeed' in publisher:
                    source = 'indeed'
                elif 'glassdoor' in publisher:
                    source = 'glassdoor'
                elif 'naukri' in publisher:
                    source = 'naukri'
                else:
                    source = publisher

                description = item.get('job_description', '')[:500]

                title   = item.get('job_title', '').strip()
                company = item.get('employer_name', 'Unknown').strip()
                loc     = f"{item.get('job_city', '')}, {item.get('job_country', '')}".strip(', ')

                if title and url:
                    jobs.append(Job(
                        title=title,
                        company=company,
                        location=loc,
                        posted_at=posted_at,
                        description=description,
                        url=url,
                        source=source,
                        country=self.country
                    ))

            return jobs

        except Exception as e:
            print(f"   ⚠️  JSearch fetch error: {e}")
            return []
