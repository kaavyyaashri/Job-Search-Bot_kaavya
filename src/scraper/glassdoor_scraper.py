import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from dateutil import parser as dateparser
from .base_scraper import BaseScraper, Job

GLASSDOOR_URL = (
    "https://www.glassdoor.com/Job/jobs.htm"
    "?sc.keyword={keyword}&locT=C&locId=1&jobType=all&fromAge=1&sort.sortType=date"
)

class GlassdoorScraper(BaseScraper):

    def scrape(self) -> list[Job]:
        all_jobs = []

        for keyword in self.keywords[:2]:
            jobs = self._fetch_jobs(keyword)
            all_jobs.extend(jobs)

        # Deduplicate by URL
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique_jobs.append(job)

        print(f"   Glassdoor → {len(unique_jobs)} unique jobs found for {self.country}")
        return unique_jobs

    def _fetch_jobs(self, keyword: str) -> list[Job]:
        url = GLASSDOOR_URL.format(keyword=keyword.replace(' ', '+'))

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            soup     = BeautifulSoup(response.text, 'lxml')
            jobs     = []

            # Glassdoor job cards
            job_cards = soup.select('li[data-test="jobListing"]')

            if not job_cards:
                # Fallback selector
                job_cards = soup.select('.react-job-listing')

            for card in job_cards[:20]:  # max 20 per keyword
                try:
                    title_el   = card.select_one('[data-test="job-title"]') or card.select_one('.job-title')
                    company_el = card.select_one('[data-test="employer-name"]') or card.select_one('.employer-name')
                    location_el= card.select_one('[data-test="emp-location"]') or card.select_one('.location')
                    link_el    = card.select_one('a[data-test="job-title"]') or card.select_one('a.jobLink')

                    title    = title_el.get_text(strip=True)    if title_el    else ''
                    company  = company_el.get_text(strip=True)  if company_el  else 'Unknown'
                    location = location_el.get_text(strip=True) if location_el else self.country
                    link     = 'https://www.glassdoor.com' + link_el['href'] if link_el and link_el.get('href') else ''

                    if title and link:
                        jobs.append(Job(
                            title=title,
                            company=company,
                            location=location,
                            posted_at=datetime.now(timezone.utc).isoformat(),
                            description='',
                            url=link,
                            source='glassdoor',
                            country=self.country
                        ))
                except Exception:
                    continue

            return jobs

        except Exception as e:
            print(f"   ⚠️  Glassdoor scrape error for '{keyword}': {e}")
            return []
