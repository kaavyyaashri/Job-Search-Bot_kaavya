import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'countries.yaml')

def load_countries():
    """Load all country configs from countries.yaml"""
    with open(CONFIG_PATH, 'r') as f:
        data = yaml.safe_load(f)
    return data['countries']

def get_country_config(country_name: str) -> dict:
    """Fetch config for a specific country by name (case-insensitive)"""
    countries = load_countries()
    for country in countries:
        if country['name'].lower() == country_name.lower():
            return country
    raise ValueError(f"Country '{country_name}' not found in countries.yaml")
