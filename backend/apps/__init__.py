"""
Backward-compatibility package alias.
Allows legacy imports like `from apps.core.models import ErrorCode`
to resolve directly to the top-level Django apps.
"""
import sys
import accounts
import assistant
import audit
import core
import faq
import integrations
import jobs
import matches
import resumes
import roadmaps
import support

_app_map = {
    'accounts': accounts,
    'assistant': assistant,
    'audit': audit,
    'core': core,
    'faq': faq,
    'integrations': integrations,
    'jobs': jobs,
    'matches': matches,
    'resumes': resumes,
    'roadmaps': roadmaps,
    'support': support,
}

for name, mod in _app_map.items():
    sys.modules[f'apps.{name}'] = mod
