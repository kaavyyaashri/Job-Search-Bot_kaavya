import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from email_sender import send_email

# Dummy jobs to test email rendering without scraping
DUMMY_JOBS = [
    {
        "rank": 1,
        "title": "Senior Software Engineer",
        "company": "Stripe",
        "location": "Remote, USA",
        "match_score": 92,
        "match_reason": "Strong Python and backend experience aligns well",
        "matched_skills": ["Python", "FastAPI", "AWS"],
        "missing_skills": ["Kubernetes"],
        "source": "LinkedIn",
        "posted_at": "2026-03-05",
        "url": "https://www.linkedin.com/jobs/view/1234567890"
    },
    {
        "rank": 2,
        "title": "Backend Engineer",
        "company": "Plaid",
        "location": "New York, NY",
        "match_score": 85,
        "match_reason": "PostgreSQL and Docker skills are a strong fit",
        "matched_skills": ["PostgreSQL", "Docker", "Python"],
        "missing_skills": ["Go"],
        "source": "Indeed",
        "posted_at": "2026-03-05",
        "url": "https://www.indeed.com/viewjob?jk=abc123"
    },
    {
        "rank": 3,
        "title": "Python Developer",
        "company": "Coinbase",
        "location": "San Francisco, CA",
        "match_score": 78,
        "match_reason": "Fintech experience and Python skills match well",
        "matched_skills": ["Python", "AWS"],
        "missing_skills": ["Rust", "Kafka"],
        "source": "LinkedIn",
        "posted_at": "2026-03-05",
        "url": "https://www.linkedin.com/jobs/view/9876543210"
    },
]

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--country', default='USA')
    args = parser.parse_args()

    print(f"\n📧 Testing Email Sender — {args.country}")
    print("=" * 50)
    send_email(DUMMY_JOBS, args.country)
