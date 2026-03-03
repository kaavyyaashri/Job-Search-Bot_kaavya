import os
import json
import google.generativeai as genai
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

def extract_text_from_docx(path: str) -> str:
    """Extract all text from a .docx file"""
    doc = Document(path)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
    return '\n'.join(full_text)

def parse_resume_with_gemini(resume_text: str) -> dict:
    """Send resume text to Gemini Flash and extract structured profile"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment/secrets")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

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

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip accidental markdown fences if Gemini adds them
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

    # 2. Parse with Gemini
    print("🤖 Sending to Gemini 1.5 Flash for parsing...")
    profile = parse_resume_with_gemini(resume_text)
    print("✅ Gemini parsing complete\n")

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
