import os
import json
from groq import Groq
from docx import Document
# ── Paths ──────────────────────────────────────────────
RESUME_PATH = os.path.join(
    os.path.dirname(__file__), '..', 
    'resumes', '01.Kaavya_Sri_Resume_2026.docx'
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), '..', 
    'data', 'resume_profile.json'
)

# ── Manual keyword additions ────────────────────────────────────────────
# resume_profile.json is fully REGENERATED every time this script runs, so
# editing that file by hand gets wiped out on the next parse. Add anything
# you want the bot to always search for here instead — it survives reruns
# and gets merged in below, on top of whatever groq extracts from the resume.
EXTRA_TARGET_TITLES = [
    # "process engineer",
    # "equipment engineer",
]
EXTRA_SKILLS = [
    # "labview",
    # "six sigma",
]

def extract_text_from_docx(path: str) -> str:
    """Extract all text from a .docx file"""
    doc = Document(path)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
    return '\n'.join(full_text)

def parse_resume_with_groq(resume_text: str) -> dict:
    """Send resume text to groq and extract structured profile"""

    api_key = os.environ.get('groq_API_KEY')
    if not api_key:
        raise ValueError("groq_API_KEY not set in environment/secrets")

    client = Groq(api_key=api_key)
    
    # genai.configure(api_key=api_key)
    # model = genai.GenerativeModel('groq-1.5-flash')

    prompt = f"""
You are a resume parser. Extract structured information from the resume below.

Return ONLY a valid JSON object — no explanation, no markdown, no code fences.

The JSON must follow this exact structure:
{{
  "target_titles": ["list of job titles this person is targeting or has held"],
  "skills": ["list of technical and soft skills"],
  "experience_years": <integer — total years of experience>,
  "seniority": "<one of: junior | mid | senior | lead>",
  "industries": ["list of industries worked in or interested in"],
  "education": "<highest degree and field>",
  "summary": "<2 sentence professional summary>"
}}

Resume:
\"\"\"
{resume_text}
\"\"\"
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",  # used before "llama-3.1-8b-instant" (deprecated) # free, fast, great at extraction
        messages=[
            {
                "role": "system",
                "content": "You are a precise resume parser. Always return valid JSON only. No markdown, no explanation."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,                        # low temp = consistent structured output
        max_tokens=1000
    )

    raw = response.choices[0].message.content.strip()

    # Strip accidental markdown fences if groq adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)

def run():
    print("\n📄 Step 2 — Resume Parser\n")

    # 1. Read DOCX
    print(f"📂 Reading resume from: {RESUME_PATH}")
    resume_text = extract_text_from_docx(RESUME_PATH)
    print(f"✅ Extracted {len(resume_text)} characters of text\n")

    # 2. Parse with groq
    print("🤖 Sending to groq 1.5 Flash for parsing...")
    profile = parse_resume_with_groq(resume_text)
    print("✅ groq parsing complete\n")

    # 2b. Merge in manual keywords — dict.fromkeys() dedupes while keeping order
    if EXTRA_TARGET_TITLES:
        profile['target_titles'] = list(dict.fromkeys(profile.get('target_titles', []) + EXTRA_TARGET_TITLES))
    if EXTRA_SKILLS:
        profile['skills'] = list(dict.fromkeys(profile.get('skills', []) + EXTRA_SKILLS))

    # 3. Save output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(profile, f, indent=2)

    print(f"💾 Saved resume profile to: {OUTPUT_PATH}")
    print("\n📊 Extracted Profile:")
    print(f"   Titles      : {profile.get('target_titles')}")
    print(f"   Skills      : {profile.get('skills')}")
    print(f"   Experience  : {profile.get('experience_years')} years")
    print(f"   Seniority   : {profile.get('seniority')}")
    print(f"   Industries  : {profile.get('industries')}")
    print(f"   Education   : {profile.get('education')}")
    print(f"   Summary     : {profile.get('summary')}\n")

if __name__ == '__main__':
    run()
