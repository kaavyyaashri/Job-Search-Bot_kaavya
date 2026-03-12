# from .base_scraper import BaseScraper, Job
# from .indeed_scraper import IndeedScraper
# from .glassdoor_scraper import GlassdoorScraper
# from .naukri_scraper import NaukriScraper

# from .base_scraper import BaseScraper, Job
# from .jsearch_scraper import JSearchScraper

from .base_scraper import BaseScraper, Job
from .jobspy_scraper import JobSpyScraper

from .jsearch_scraper import JSearchScraper

def get_scraper(country_config: dict, country_name: str):
    """Return list of scrapers to run for this country"""
    scrapers = [
        JobSpyScraper(country_config, country_name),
        JSearchScraper(country_config, country_name),
    ]
    return scrapers
