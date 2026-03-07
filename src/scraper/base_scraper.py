from abc import ABC, abstractmethod
from dataclasses import dataclass
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
    def __init__(self, country_config: dict):
        self.country        = country_config['name']
        self.keywords       = country_config['search_keywords']
        self.locations      = country_config['location_keywords']
        self.country_config = country_config          # ← store full config

    @abstractmethod
    def scrape(self) -> list[Job]:
        pass

    def to_dict_list(self, jobs: list[Job]) -> list[dict]:
        return [vars(j) for j in jobs]


# from abc import ABC, abstractmethod
# from dataclasses import dataclass
# from datetime import datetime

# @dataclass
# class Job:
#     title: str
#     company: str
#     location: str
#     posted_at: str          # ISO format string
#     description: str        # first 500 chars
#     url: str
#     source: str             # "linkedin" | "glassdoor" | "naukri"
#     country: str

# class BaseScraper(ABC):
#     def __init__(self, country_config: dict):
#         self.country = country_config['name']
#         self.keywords = country_config['search_keywords']
#         self.locations = country_config['location_keywords']

#     @abstractmethod
#     def scrape(self) -> list[Job]:
#         """Each scraper must implement this and return a list of Job objects"""
#         pass

#     def to_dict_list(self, jobs: list[Job]) -> list[dict]:
#         return [vars(j) for j in jobs]
