import re
from apps.resumes.seed_taxonomy import DEFAULT_TAXONOMY
from apps.resumes.models import Skill
from .models import Job, JobRequirement

PREFERRED_MARKERS = [
    r'\bnice\s+to\s+have\b',
    r'\bpreferred\b',
    r'\bbonus\b',
    r'\bplus\b',
    r'\bdesirable\b',
    r'\boptional\b',
    r'\bwould\s+be\s+great\b',
    r'\bideal\b'
]

MANDATORY_MARKERS = [
    r'\brequired\b',
    r'\bmust\s+have\b',
    r'\bessential\b',
    r'\bminimum\b',
    r'\bproficiency\s+in\b',
    r'\bstrong\s+experience\b',
    r'\bresponsibilities\b',
    r'\bqualifications\b'
]

def extract_job_requirements(job: Job):
    """
    Scans job description text, identifies taxonomy skills, determines
    whether sentence context indicates mandatory vs preferred, and saves JobRequirements.
    """
    job.requirements.all().delete()
    text = job.description
    sentences = re.split(r'[.\n;]+', text)

    found_skills = {}

    for sentence in sentences:
        clean_sentence = sentence.strip()
        if not clean_sentence:
            continue

        sentence_lower = clean_sentence.lower()

        is_preferred = any(re.search(pat, sentence_lower) for pat in PREFERRED_MARKERS)
        is_mandatory = any(re.search(pat, sentence_lower) for pat in MANDATORY_MARKERS)

        # Default to mandatory unless explicitly marked preferred
        mandatory_flag = not is_preferred

        for entry in DEFAULT_TAXONOMY:
            canonical_name = entry["name"]
            aliases = [canonical_name.lower()] + [a.lower() for a in entry["aliases"]]

            for alias in aliases:
                escaped = re.escape(alias)
                if alias in ('c++', 'c#'):
                    pattern = rf'(?:^|[\s,;:(])({escaped})(?:$|[\s,;:).])'
                elif alias in ('go',):
                    pattern = rf'\b(golang|go\s+language)\b'
                else:
                    pattern = rf'\b({escaped})\b'

                if re.search(pattern, clean_sentence, re.IGNORECASE):
                    if canonical_name not in found_skills:
                        found_skills[canonical_name] = {
                            'name': canonical_name,
                            'is_mandatory': mandatory_flag,
                            'weight': 1.0 if mandatory_flag else 0.5,
                            'evidence': clean_sentence[:450],
                        }
                    else:
                        # If previously recorded as preferred but another sentence marks it mandatory, elevate it
                        if mandatory_flag and not found_skills[canonical_name]['is_mandatory']:
                            found_skills[canonical_name]['is_mandatory'] = True
                            found_skills[canonical_name]['weight'] = 1.0
                            found_skills[canonical_name]['evidence'] = clean_sentence[:450]
                    break

    for skill_name, data in found_skills.items():
        canonical_skill = Skill.objects.filter(name__iexact=skill_name).first()
        JobRequirement.objects.create(
            job=job,
            skill=canonical_skill,
            skill_name=skill_name,
            is_mandatory=data['is_mandatory'],
            importance_weight=data['weight'],
            evidence_text=data['evidence']
        )
