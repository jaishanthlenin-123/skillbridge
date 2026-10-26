import re
from typing import List, Dict
from ml_service.app.schemas.extraction import (
    ResumeExtractionRequest, ResumeExtractionResponse,
    ExtractedSkill, ExtractedSection,
    JobExtractionRequest, JobExtractionResponse, ExtractedRequirement
)

TAXONOMY_DICTIONARY = [
    {"name": "Python", "category": "languages", "aliases": ["python", "python3", "py"]},
    {"name": "JavaScript", "category": "languages", "aliases": ["javascript", "js"]},
    {"name": "TypeScript", "category": "languages", "aliases": ["typescript", "ts"]},
    {"name": "Java", "category": "languages", "aliases": ["java", "core java"]},
    {"name": "C++", "category": "languages", "aliases": ["c++", "cpp"]},
    {"name": "Go", "category": "languages", "aliases": ["golang", "go language"]},
    {"name": "Rust", "category": "languages", "aliases": ["rust", "rustlang"]},
    {"name": "SQL", "category": "languages", "aliases": ["sql"]},
    {"name": "HTML", "category": "languages", "aliases": ["html", "html5"]},
    {"name": "CSS", "category": "languages", "aliases": ["css", "css3"]},
    {"name": "React", "category": "frameworks", "aliases": ["react", "react.js", "reactjs"]},
    {"name": "Next.js", "category": "frameworks", "aliases": ["next.js", "nextjs"]},
    {"name": "Django", "category": "frameworks", "aliases": ["django", "drf"]},
    {"name": "FastAPI", "category": "frameworks", "aliases": ["fastapi"]},
    {"name": "Flask", "category": "frameworks", "aliases": ["flask"]},
    {"name": "Node.js", "category": "frameworks", "aliases": ["node", "node.js", "nodejs"]},
    {"name": "Tailwind CSS", "category": "frameworks", "aliases": ["tailwind", "tailwindcss"]},
    {"name": "PostgreSQL", "category": "databases", "aliases": ["postgres", "postgresql"]},
    {"name": "MySQL", "category": "databases", "aliases": ["mysql"]},
    {"name": "MongoDB", "category": "databases", "aliases": ["mongodb", "mongo"]},
    {"name": "Redis", "category": "databases", "aliases": ["redis"]},
    {"name": "Docker", "category": "cloud_infra", "aliases": ["docker"]},
    {"name": "Kubernetes", "category": "cloud_infra", "aliases": ["kubernetes", "k8s"]},
    {"name": "AWS", "category": "cloud_infra", "aliases": ["aws", "amazon web services"]},
    {"name": "Azure", "category": "cloud_infra", "aliases": ["azure"]},
    {"name": "GCP", "category": "cloud_infra", "aliases": ["gcp", "google cloud"]},
    {"name": "Terraform", "category": "cloud_infra", "aliases": ["terraform"]},
    {"name": "Linux", "category": "cloud_infra", "aliases": ["linux", "ubuntu"]},
    {"name": "CI/CD", "category": "cloud_infra", "aliases": ["ci/cd", "continuous integration", "github actions"]},
    {"name": "PyTorch", "category": "ml_nlp", "aliases": ["pytorch", "torch"]},
    {"name": "TensorFlow", "category": "ml_nlp", "aliases": ["tensorflow", "tf"]},
    {"name": "scikit-learn", "category": "ml_nlp", "aliases": ["scikit-learn", "sklearn"]},
    {"name": "Hugging Face", "category": "ml_nlp", "aliases": ["hugging face", "huggingface", "transformers"]},
    {"name": "REST APIs", "category": "dev_tools", "aliases": ["rest", "rest api", "restful"]},
    {"name": "Git", "category": "dev_tools", "aliases": ["git", "github"]},
]

SECTION_KEYWORDS = [
    ('SUMMARY', re.compile(r'^(summary|professional summary|about|profile)\b', re.IGNORECASE)),
    ('EXPERIENCE', re.compile(r'^(experience|work experience|employment history)\b', re.IGNORECASE)),
    ('EDUCATION', re.compile(r'^(education|academics|qualifications)\b', re.IGNORECASE)),
    ('SKILLS', re.compile(r'^(skills|technical skills|technologies)\b', re.IGNORECASE)),
    ('PROJECTS', re.compile(r'^(projects|technical projects)\b', re.IGNORECASE)),
]

def extract_resume_pipeline(req: ResumeExtractionRequest) -> ResumeExtractionResponse:
    text = req.text.strip()
    if len(text) < 20:
        return ResumeExtractionResponse(
            raw_text=text,
            sections=[],
            skills=[],
            has_scanned_content_warning=True
        )

    # Segment sections
    sections = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    curr_type = 'SUMMARY'
    curr_lines = []

    for line in lines:
        matched = None
        if len(line) < 50:
            for stype, pat in SECTION_KEYWORDS:
                if pat.search(line):
                    matched = stype
                    break
        if matched:
            if curr_lines:
                sections.append(ExtractedSection(type=curr_type, content="\n".join(curr_lines)))
                curr_lines = []
            curr_type = matched
        else:
            curr_lines.append(line)

    if curr_lines:
        sections.append(ExtractedSection(type=curr_type, content="\n".join(curr_lines)))

    # Extract skills
    extracted_skills = []
    for item in TAXONOMY_DICTIONARY:
        patterns = [item["name"].lower()] + [a.lower() for a in item["aliases"]]
        for alias in patterns:
            escaped = re.escape(alias)
            if alias in ('c++', 'c#'):
                pattern = rf'(?:^|[\s,;:(])({escaped})(?:$|[\s,;:).])'
            elif alias == 'go':
                pattern = rf'\b(golang|go\s+language)\b'
            else:
                pattern = rf'\b({escaped})\b'

            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                start = max(0, m.start() - 40)
                end = min(len(text), m.end() + 40)
                snip = text[start:end].replace('\n', ' ')
                extracted_skills.append(
                    ExtractedSkill(
                        name=item["name"],
                        category=item["category"],
                        evidence=f"...{snip}...",
                        confidence=0.95
                    )
                )
                break

    return ResumeExtractionResponse(
        raw_text=text,
        sections=sections,
        skills=extracted_skills,
        has_scanned_content_warning=False
    )

def extract_job_pipeline(req: JobExtractionRequest) -> JobExtractionResponse:
    text = req.job_description
    sentences = re.split(r'[.\n;]+', text)
    requirements = []
    seen = set()

    preferred_pat = re.compile(r'\b(preferred|nice to have|plus|bonus|optional)\b', re.IGNORECASE)

    for sentence in sentences:
        s_clean = sentence.strip()
        if not s_clean:
            continue
        is_pref = bool(preferred_pat.search(s_clean))
        is_mand = not is_pref

        for item in TAXONOMY_DICTIONARY:
            canonical = item["name"]
            if canonical in seen:
                continue

            patterns = [canonical.lower()] + [a.lower() for a in item["aliases"]]
            for alias in patterns:
                escaped = re.escape(alias)
                if alias in ('c++', 'c#'):
                    pat = rf'(?:^|[\s,;:(])({escaped})(?:$|[\s,;:).])'
                elif alias == 'go':
                    pat = rf'\b(golang|go\s+language)\b'
                else:
                    pat = rf'\b({escaped})\b'

                if re.search(pat, s_clean, re.IGNORECASE):
                    seen.add(canonical)
                    requirements.append(
                        ExtractedRequirement(
                            skill_name=canonical,
                            is_mandatory=is_mand,
                            importance_weight=1.0 if is_mand else 0.5,
                            evidence_text=s_clean[:400]
                        )
                    )
                    break

    return JobExtractionResponse(requirements=requirements)
