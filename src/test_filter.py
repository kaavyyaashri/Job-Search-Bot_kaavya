import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from job_filter import filter_jobs, is_job_excluded

# Test cases — mix of jobs that should and should not be filtered
TEST_JOBS = [
    {
        "title": "Software Engineer",
        "company": "Google",
        "description": "We are looking for a software engineer to join our team. We offer visa sponsorship.",
        "url": "https://example.com/1"
    },
    {
        "title": "Electrical Engineer",
        "company": "Lockheed Martin",
        "description": "Must be a US Citizen. Secret clearance required. No OPT candidates.",
        "url": "https://example.com/2"
    },
    {
        "title": "Backend Developer",
        "company": "Stripe",
        "description": "Great role for backend developers. No sponsorship available for this position.",
        "url": "https://example.com/3"
    },
    {
        "title": "Testing Engineer",
        "company": "Texas Instruments",
        "description": "Exciting testing role. Open to all work authorizations. Will not sponsor visas.",
        "url": "https://example.com/4"
    },
    {
        "title": "Product Engineer",
        "company": "Apple",
        "description": "Product engineering role. Green card or citizenship required.",
        "url": "https://example.com/5"
    },
    {
        "title": "Senior Engineer",
        "company": "Anthropic",
        "description": "We are willing to sponsor H1B visas for exceptional candidates.",
        "url": "https://example.com/6"
    },
]

def test_filter():
    print("\n🧪 Testing Job Filter")
    print("=" * 60)

    eligible, excluded = filter_jobs(TEST_JOBS)

    print(f"\n✅ Eligible ({len(eligible)} jobs):")
    for job in eligible:
        print(f"   ✅ {job['title']} @ {job['company']}")

    print(f"\n🚫 Excluded ({len(excluded)} jobs):")
    for job in excluded:
        print(f"   ❌ {job['title']} @ {job['company']}")
        print(f"      Reason: '{job['excluded_reason']}'")

    print("\n" + "=" * 60)
    print("Expected results:")
    print("   ✅ Google       — 'willing to sponsor' is a SAFE phrase")
    print("   ❌ Lockheed     — 'us citizen' + 'secret clearance' + 'no opt'")
    print("   ❌ Stripe       — 'no sponsorship'")
    print("   ❌ TI           — 'will not sponsor'")
    print("   ❌ Apple        — 'green card'")
    print("   ✅ Anthropic    — 'willing to sponsor' is a SAFE phrase")

if __name__ == '__main__':
    test_filter()
