import requests
import feedparser
from datetime import datetime, timezone
from dateutil import parser as dateparser
from .base_scraper import BaseScraper, Job

# Indeed RSS — free, no auth, reliable
# fromage=1 → posted in last 1 day
INDEED_RSS = "https://www.indeed.com/rss?q={keyword}&l={location}&fromage=1&sort=date"

class IndeedScraper(BaseScraper):

    def scrape(self) -> list[Job]:
        all_jobs = []

        for keyword in self.keywords[:2]:
            for location in self.locations[:2]:
                jobs = self._fetch_rss(keyword, location)
                all_jobs.extend(jobs)

        # Deduplicate by URL
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique_jobs.append(job)

        print(f"   Indeed → {len(unique_jobs)} unique jobs found for {self.country}")
        return unique_jobs

    def _fetch_rss(self, keyword: str, location: str) -> list[Job]:
        url = INDEED_RSS.format(
            keyword=keyword.replace(' ', '+'),
            location=location.replace(' ', '+')
        )

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            feed     = feedparser.parse(response.content)
            jobs     = []

            for entry in feed.entries:
                title       = entry.get('title', '').strip()
                link        = entry.get('link', '').strip()
                summary     = entry.get('summary', '')[:500]
                pub_date    = entry.get('published', '')
                company     = entry.get('source', {}).get('title', 'Unknown')

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
                        source='indeed',
                        country=self.country
                    ))

            return jobs

        except Exception as e:
            print(f"   ⚠️  Indeed RSS error for '{keyword}' / '{location}': {e}")
            return []
