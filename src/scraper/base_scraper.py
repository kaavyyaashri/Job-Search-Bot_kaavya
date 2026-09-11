from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Job:
    title: str
    company: str
    location: str
    posted_at: str
    description: str
    url: str
    source: str
    country: str
    easy_apply: bool = False

class BaseScraper(ABC):
    def __init__(self, country_config: dict,country_name: str):
        self.country        = country_name
        self.keywords       = country_config['search_keywords']
        self.locations      = country_config['location_keywords']
        self.country_config = country_config          # ← store full config

    @abstractmethod
    def scrape(self) -> list[Job]:
        pass

    def to_dict_list(self, jobs: list[Job]) -> list[dict]:
        return [vars(j) for j in jobs]

    def dedupe_by_url(self, jobs: list[Job]) -> list[Job]:
        """Shared by every scraper — dedupe a job list by URL, keeping first seen."""
        seen = set()
        unique = []
        for job in jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique.append(job)
        return unique

