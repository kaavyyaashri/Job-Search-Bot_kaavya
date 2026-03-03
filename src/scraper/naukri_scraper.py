import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from .base_scraper import BaseScraper, Job

NAUKRI_URL = "https://www.naukri.com/{keyword}-jobs-in-{location}?jobAge=1"

class NaukriScraper(BaseScraper):

    def scrape(self) -> list[Job]:
        all_jobs = []

        for keyword in self.keywords[:2]:
            for location in self.locations[:2]:
                jobs = self._fetch_jobs(keyword, location)
                all_jobs.extend(jobs)

        # Deduplicate by URL
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique_jobs.append(job)

        print(f"   Naukri → {len(unique_jobs)} unique jobs found for {self.country}")
        return unique_jobs

    def _fetch_jobs(self, keyword: str, location: str) -> list[Job]:
        slug_keyword  = keyword.lower().replace(' ', '-')
        slug_location = location.lower().replace(' ', '-')
        url = NAUKRI_URL.format(keyword=slug_keyword, location=slug_location)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml",
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            soup     = BeautifulSoup(response.text, 'lxml')
            jobs     = []

            # Naukri job cards
            job_cards = soup.select('article.jobTuple') or soup.select('.cust-job-tuple')

            for card in job_cards[:20]:
                try:
                    title_el   = card.select_one('a.title') or card.select_one('.title')
                    company_el = card.select_one('a.subTitle') or card.select_one('.companyInfo .subTitle')
                    location_el= card.select_one('.locWdth') or card.select_one('.location')
                    link_el    = card.select_one('a.title')

                    title    = title_el.get_text(strip=True)    if title_el    else ''
                    company  = company_el.get_text(strip=True)  if company_el  else 'Unknown'
                    loc_text = location_el.get_text(strip=True) if location_el else location
                    link     = link_el['href']                  if link_el and link_el.get('href') else ''

                    # Make sure URL is absolute
                    if link and not link.startswith('http'):
                        link = 'https://www.naukri.com' + link

                    if title and link:
                        jobs.append(Job(
                            title=title,
                            company=company,
                            location=loc_text,
                            posted_at=datetime.now(timezone.utc).isoformat(),
                            description='',
                            url=link,
                            source='naukri',
                            country=self.country
                        ))
                except Exception:
                    continue

            return jobs

        except Exception as e:
            print(f"   ⚠️  Naukri scrape error for '{keyword}' / '{location}': {e}")
            return []
