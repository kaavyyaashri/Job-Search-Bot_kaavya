import os
import json
import requests
from datetime import datetime, timezone
from .base_scraper import BaseScraper, Job

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"

COUNTRY_FILTER = {
    "USA":       "us",
    "India":     "in",
    "Singapore": "sg",
    "Ireland":    "ie",
}

# def load_resume_titles() -> list[str]:
#     try:
#         with open(RESUME_PROFILE_PATH, 'r') as f:
#             profile = json.load(f)
#         return profile.get('target_titles', [])[:2]
#     except Exception:
#         return ["product engineer", "test engineer"]
        
class JSearchScraper(BaseScraper):

    def scrape(self) -> list[Job]:
        api_key = os.environ.get("RAPIDAPI_KEY", "")
        if not api_key:
            print("   ⚠️  RAPIDAPI_KEY not set — skipping JSearch")
            return []

        # Use same search_keywords from countries.yaml as JobSpy — consistent coverage
        search_terms = self.country_config.get('search_keywords', [])
        if not search_terms:
            print("   ⚠️  No search_keywords in countries.yaml — skipping JSearch")
            return []
        print(f"   📄 JSearch: {len(search_terms)} keywords loaded from countries.yaml")

        all_jobs = []
        for term in search_terms:
            jobs = self._fetch_jobs(api_key, term)
            all_jobs.extend(jobs)

        # Deduplicate by URL
        seen        = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique_jobs.append(job)

        print(f"   JSearch → {len(unique_jobs)} unique jobs found for {self.country}")
        return unique_jobs

    def _fetch_jobs(self, api_key: str, search_term: str) -> list[Job]:
        location     = self.locations[0] if self.locations else self.country
        country_code = COUNTRY_FILTER.get(self.country, "us")
        query        = f"{search_term} in {location}"

        print(f"   🔎 JSearch: '{query}'...")

        headers = {
            "X-RapidAPI-Key":  api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        params = {
            "query":               query,
            "page":                "1",
            "num_pages":           "1",
            "country":             country_code,
            "date_posted":         "today",
            "employment_types":    "FULLTIME",
        }

        try:
            response = requests.get(
                JSEARCH_URL, headers=headers, params=params, timeout=15
            )

            if response.status_code != 200:
                print(f"   ⚠️  JSearch error: HTTP {response.status_code}")
                return []

            data = response.json().get("data", [])
            if not data:
                print(f"   ⚠️  JSearch: no results for '{query}'")
                return []

            jobs = []
            for item in data:
                try:
                    title   = str(item.get("job_title",       "") or "").strip()
                    company = str(item.get("employer_name",   "") or "Unknown").strip()
                    loc_str = str(item.get("job_city",        "") or location).strip()
                    desc    = str(item.get("job_description", "") or "")[:1500]
                    url     = str(item.get("job_apply_link",  "") or "").strip()

                    # Posted date
                    ts = item.get("job_posted_at_timestamp")
                    if ts:
                        posted_at = datetime.fromtimestamp(
                            int(ts), tz=timezone.utc
                        ).isoformat()
                    else:
                        posted_at = datetime.now(timezone.utc).isoformat()

                    # Easy apply detection
                    apply_options = item.get("apply_options", [])
                    easy_apply    = any(
                        "linkedin" in str(o.get("publisher", "")).lower()
                        and o.get("is_direct", False) is False
                        for o in apply_options
                    )

                    if not title or not url:
                        continue

                    # ── Freshness filter — skip jobs older than 24 hours ────
                    try:
                        posted_dt = datetime.fromisoformat(str(posted_at))
                        if posted_dt.tzinfo is None:
                            posted_dt = posted_dt.replace(tzinfo=timezone.utc)
                        age_hours = (datetime.now(timezone.utc) - posted_dt).total_seconds() / 3600
                        if age_hours > 24:
                            continue
                    except Exception:
                        pass
                    #----------------------------------------------------------- 
                    jobs.append(Job(
                        title=title,
                        company=company,
                        location=loc_str,
                        posted_at=posted_at,
                        description=desc,
                        url=url,
                        source="jsearch",
                        country=self.country,
                        easy_apply=easy_apply,
                    ))

                except Exception:
                    continue

            return jobs

        except Exception as e:
            print(f"   ⚠️  JSearch request failed: {e}")
            return []
