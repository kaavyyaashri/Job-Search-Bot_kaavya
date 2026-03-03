import sys, os, requests, feedparser
from bs4 import BeautifulSoup
sys.path.insert(0, os.path.dirname(__file__))

def debug_indeed():
    print("\n🔍 DEBUG — Indeed RSS")
    print("=" * 50)

    url = "https://www.indeed.com/rss?q=software+engineer&l=United+States&fromage=1&sort=date"
    print(f"URL: {url}\n")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    response = requests.get(url, headers=headers, timeout=15)

    print(f"Status Code  : {response.status_code}")
    print(f"Content-Type : {response.headers.get('content-type', 'unknown')}")
    print(f"Response Size: {len(response.content)} bytes")
    print(f"\nFirst 500 chars of response:")
    print(response.text[:500])
    print("\n--- feedparser result ---")
    feed = feedparser.parse(response.content)
    print(f"Feed title   : {feed.feed.get('title', 'none')}")
    print(f"Entries found: {len(feed.entries)}")
    if feed.entries:
        print(f"\nFirst entry:")
        print(f"  title    : {feed.entries[0].get('title', '')}")
        print(f"  link     : {feed.entries[0].get('link', '')}")
        print(f"  published: {feed.entries[0].get('published', '')}")


def debug_glassdoor():
    print("\n\n🔍 DEBUG — Glassdoor")
    print("=" * 50)

    url = "https://www.glassdoor.com/Job/jobs.htm?sc.keyword=software+engineer&fromAge=1&sort.sortType=date"
    print(f"URL: {url}\n")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    }

    response = requests.get(url, headers=headers, timeout=15)

    print(f"Status Code  : {response.status_code}")
    print(f"Content-Type : {response.headers.get('content-type', 'unknown')}")
    print(f"Response Size: {len(response.content)} bytes")
    print(f"\nFirst 500 chars of response:")
    print(response.text[:500])

    soup = BeautifulSoup(response.text, 'lxml')

    # Try multiple selectors and report which ones find anything
    selectors = [
        'li[data-test="jobListing"]',
        '.react-job-listing',
        '[data-test="job-title"]',
        'article.job-listing',
        '.JobCard',
        'div[data-jobid]',
    ]
    print("\n--- Selector results ---")
    for sel in selectors:
        found = soup.select(sel)
        print(f"  {sel!r:45} → {len(found)} elements")


def debug_naukri():
    print("\n\n🔍 DEBUG — Naukri")
    print("=" * 50)

    url = "https://www.naukri.com/software-engineer-jobs-in-bangalore?jobAge=1"
    print(f"URL: {url}\n")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    }

    response = requests.get(url, headers=headers, timeout=15)

    print(f"Status Code  : {response.status_code}")
    print(f"Content-Type : {response.headers.get('content-type', 'unknown')}")
    print(f"Response Size: {len(response.content)} bytes")
    print(f"\nFirst 500 chars of response:")
    print(response.text[:500])

    soup = BeautifulSoup(response.text, 'lxml')

    selectors = [
        'article.jobTuple',
        '.cust-job-tuple',
        '.job-tuple',
        '[data-job-id]',
        '.srp-jobtuple-wrapper',
        'a.title',
    ]
    print("\n--- Selector results ---")
    for sel in selectors:
        found = soup.select(sel)
        print(f"  {sel!r:45} → {len(found)} elements")


if __name__ == '__main__':
    debug_indeed()
    debug_glassdoor()
    debug_naukri()
