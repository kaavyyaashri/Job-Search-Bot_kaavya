import os
import json
import re
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RESUME_PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'resume_profile.json'
)

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def load_resume_profile() -> dict:
    with open(RESUME_PROFILE_PATH, 'r') as f:
        return json.load(f)

def build_resume_text(profile: dict) -> str:
    """
    Flatten resume profile into a single string for TF-IDF comparison.
    The richer this string, the better the matching.
    """
    parts = []
    parts.extend(profile.get('target_titles', []))
    parts.extend(profile.get('skills', []))
    parts.append(profile.get('seniority', ''))
    parts.extend(profile.get('industries', []))
    parts.append(profile.get('education', ''))
    parts.append(profile.get('summary', ''))
    return ' '.join(p for p in parts if p)

def build_job_text(job: dict) -> str:
    """
    Flatten job into a single string for TF-IDF comparison.
    Title weighted 3x because it's the strongest signal.
    """
    title       = job.get('title', '')
    company     = job.get('company', '')
    description = job.get('description', '')
    location    = job.get('location', '')
    # Repeat title 3x to give it more weight in TF-IDF
    return f"{title} {title} {title} {company} {description} {location}"

# ─────────────────────────────────────────
# STAGE 1 — TF-IDF COSINE SIMILARITY
# ─────────────────────────────────────────

def tfidf_score(jobs: list[dict], resume_text: str) -> list[dict]:
    """
    Score all jobs against resume using TF-IDF cosine similarity.
    Returns jobs sorted by score, highest first.
    """
    if not jobs:
        return []

    job_texts   = [build_job_text(j) for j in jobs]
    all_texts   = [resume_text] + job_texts     # resume is index 0

    vectorizer  = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),                     # unigrams + bigrams
        max_features=5000
    )

    tfidf_matrix = vectorizer.fit_transform(all_texts)
    resume_vec   = tfidf_matrix[0]              # resume vector
    job_vecs     = tfidf_matrix[1:]             # job vectors

    scores = cosine_similarity(resume_vec, job_vecs)[0]

    # Attach scores to jobs
    scored_jobs = []
    for job, score in zip(jobs, scores):
        job_copy = job.copy()
        job_copy['tfidf_score'] = round(float(score), 4)
        scored_jobs.append(job_copy)

    # Sort by score descending
    scored_jobs.sort(key=lambda x: x['tfidf_score'], reverse=True)

    print(f"   ✅ TF-IDF scoring complete — top score: {scored_jobs[0]['tfidf_score']:.4f}")
    return scored_jobs

# ─────────────────────────────────────────
# STAGE 2 — GROQ RE-RANKING
# ─────────────────────────────────────────

def groq_rerank(top_jobs: list[dict], profile: dict) -> list[dict]:
    """
    Send top 20 TF-IDF jobs to Groq for intelligent re-ranking.
    Returns top 10 with match scores and skill breakdowns.
    """
    api_key = os.environ.get('GROQ_API_KEY', '').strip()
    if not api_key:
        print("   ⚠️  GROQ_API_KEY not set — skipping re-rank, using TF-IDF top 10")
        return top_jobs[:10]

    client = Groq(api_key=api_key)

    # Build a compact job list for the prompt (avoid token overflow)
    job_summaries = []
    for i, job in enumerate(top_jobs, 1):
        job_summaries.append(
            f"{i}. Title: {job['title']} | Company: {job['company']} | "
            f"Location: {job['location']} | "
            f"Description: {job.get('description', '')[:200]}"
        )

    jobs_text   = '\n'.join(job_summaries)
    skills_text = ', '.join(profile.get('skills', []))
    titles_text = ', '.join(profile.get('target_titles', []))

    prompt = f"""You are a job matching expert. Given a candidate's profile and a list of job postings, rank the TOP 10 most relevant jobs.

Candidate Profile:
- Target titles: {titles_text}
- Skills: {skills_text}
- Seniority: {profile.get('seniority', 'mid')}
- Industries: {', '.join(profile.get('industries', []))}

Job Postings:
{jobs_text}

Return ONLY a valid JSON array — no explanation, no markdown, no code fences.
Each item must have exactly these fields:
{{
  "rank": <1-10>,
  "job_number": <the number from the list above>,
  "match_score": <integer 0-100>,
  "match_reason": "<one sentence why this matches>",
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3"]
}}

Return exactly 10 items ranked from best to worst match.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise job matching assistant. Always return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=2000
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        rankings = json.loads(raw)

        # Map rankings back to full job objects
        final_jobs = []
        for rank_item in rankings:
            job_idx = rank_item.get('job_number', 1) - 1
            if 0 <= job_idx < len(top_jobs):
                job_copy = top_jobs[job_idx].copy()
                job_copy['rank']           = rank_item.get('rank', len(final_jobs) + 1)
                job_copy['match_score']    = rank_item.get('match_score', 0)
                job_copy['match_reason']   = rank_item.get('match_reason', '')
                job_copy['matched_skills'] = rank_item.get('matched_skills', [])
                job_copy['missing_skills'] = rank_item.get('missing_skills', [])
                final_jobs.append(job_copy)

        print(f"   ✅ Groq re-ranking complete — top match score: {final_jobs[0]['match_score']}%")
        return final_jobs[:10]

    except Exception as e:
        print(f"   ⚠️  Groq re-ranking failed: {e} — falling back to TF-IDF top 10")
        # Fallback — return TF-IDF top 10 with dummy score fields
        fallback = []
        for i, job in enumerate(top_jobs[:10], 1):
            job_copy = job.copy()
            job_copy['rank']           = i
            job_copy['match_score']    = round(job.get('tfidf_score', 0) * 100)
            job_copy['match_reason']   = 'Matched via TF-IDF keyword similarity'
            job_copy['matched_skills'] = []
            job_copy['missing_skills'] = []
            fallback.append(job_copy)
        return fallback

# ─────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────

def score_and_rank(jobs: list[dict]) -> list[dict]:
    """
    Full scoring pipeline:
      1. Load resume profile
      2. TF-IDF filter → top 20
      3. Groq re-rank → top 10
    Returns final top 10 jobs with scores and skill breakdowns.
    """
    print(f"\n📊 Scoring {len(jobs)} jobs against resume...\n")

    if not jobs:
        print("   ⚠️  No jobs to score")
        return []

    # 1. Load resume
    profile     = load_resume_profile()
    resume_text = build_resume_text(profile)
    print(f"   📄 Resume profile: {profile.get('target_titles')} | {len(profile.get('skills', []))} skills")

    # 2. TF-IDF → top 20
    print(f"\n   Stage 1 — TF-IDF scoring {len(jobs)} jobs...")
    scored      = tfidf_score(jobs, resume_text)
    top_20      = scored[:20]
    print(f"   Filtered to top 20 candidates\n")

    # 3. Groq re-rank → top 10
    print(f"   Stage 2 — Groq re-ranking top 20...")
    top_10      = groq_rerank(top_20, profile)

    print(f"\n✅ Final top {len(top_10)} jobs selected\n")
    return top_10
