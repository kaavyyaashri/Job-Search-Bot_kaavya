import feedparser
import requests
from datetime import datetime, timezone
from dateutil import parser as dateparser
from .base_scraper import BaseScraper, Job

# LinkedIn RSS URL template
# f_TPR=r86400 → posted in last 24 hours
# keywords and location are injected per country
LINKEDIN_RSS = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    "?keywords={keywords}&location={location}&f_TPR=r86400&start=0"
)

LINKEDIN_RSS_FEED = (
    "https://www.linkedin.com/jobs/search/rss"
    "?keywords={keywords}&location={location}&f_TPR=r86400"
)

class LinkedInScraper(BaseScraper):

    def scrape(self) -> list[Job]:
        all_jobs = []

        for keyword in self.keywords[:2]:           # top 2 keywords to stay within limits
            for location in self.locations[:2]:     # top 2 locations
                jobs = self._fetch_rss(keyword, location)
                all_jobs.extend(jobs)

        # Deduplicate by URL
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique_jobs.append(job)

        print(f"   LinkedIn → {len(unique_jobs)} unique jobs found for {self.country}")
        return unique_jobs

    def _fetch_rss(self, keyword: str, location: str) -> list[Job]:
        url = LINKEDIN_RSS_FEED.format(
            keywords=keyword.replace(' ', '+'),
            location=location.replace(' ', '+')
        )

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; RSS reader)"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            feed = feedparser.parse(response.content)
            jobs = []

            for entry in feed.entries:
                title    = entry.get('title', '').strip()
                link     = entry.get('link', '').strip()
                summary  = entry.get('summary', '')[:500]
                pub_date = entry.get('published', '')

                # Parse company and location from title
                # LinkedIn RSS title format: "Job Title at Company"
                company = ''
                if ' at ' in title:
                    parts   = title.rsplit(' at ', 1)
                    title   = parts[0].strip()
                    company = parts[1].strip()

                # Normalize date
                try:
                    posted_at = dateparser.parse(pub_date).isoformat()
                except Exception:
                    posted_at = datetime.now(timezone.utc).isoformat()

                if title and link:
                    jobs.append(Job(
                        title=title,
                        company=company,
                        location=location,
                        posted_at=posted_at,
                        description=summary,
                        url=link,
                        source='linkedin',
                        country=self.country
                    ))

            return jobs

        except Exception as e:
            print(f"   ⚠️  LinkedIn RSS error for '{keyword}' / '{location}': {e}")
            return []
