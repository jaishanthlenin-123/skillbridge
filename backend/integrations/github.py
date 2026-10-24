import os
import requests
import logging

logger = logging.getLogger('skillbridge.integrations.github')

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TIMEOUT_SECONDS = 5.0

def fetch_github_user_profile(username: str) -> dict:
    """
    Fetches public profile data and top repositories from GitHub REST API.
    Enforces a strict 5-second timeout and provides graceful fallbacks for rate limits,
    404s, or network downtime.
    """
    clean_username = username.strip().lstrip('@')
    if not clean_username:
        return {'status': 'error', 'message': 'Username cannot be empty.'}

    token = os.getenv('GITHUB_API_TOKEN', '').strip()
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'SkillBridge-ResumeMatcher/1.0',
    }
    if token:
        headers['Authorization'] = f"token {token}"

    user_url = f"{GITHUB_API_BASE}/users/{clean_username}"
    repos_url = f"{GITHUB_API_BASE}/users/{clean_username}/repos?sort=updated&per_page=10"

    try:
        # 1. Fetch user profile
        user_resp = requests.get(user_url, headers=headers, timeout=GITHUB_TIMEOUT_SECONDS)
        
        if user_resp.status_code == 404:
            return {'status': 'not_found', 'message': f"GitHub user '{clean_username}' was not found."}
        if user_resp.status_code == 403:
            return {
                'status': 'rate_limited',
                'message': 'GitHub API rate limit exceeded. Please try again later or configure GITHUB_API_TOKEN.',
                'username': clean_username
            }
        user_resp.raise_for_status()
        user_data = user_resp.json()

        # 2. Fetch recent public repositories
        repos_resp = requests.get(repos_url, headers=headers, timeout=GITHUB_TIMEOUT_SECONDS)
        repos_data = repos_resp.json() if repos_resp.status_code == 200 else []

        languages_detected = set()
        topics_detected = set()
        total_stars = 0
        repo_summaries = []

        for repo in repos_data:
            if not repo.get('fork', False):
                lang = repo.get('language')
                if lang:
                    languages_detected.add(lang)
                for topic in repo.get('topics', []):
                    topics_detected.add(topic)
                total_stars += repo.get('stargazers_count', 0)
                repo_summaries.append({
                    'name': repo.get('name'),
                    'description': repo.get('description') or '',
                    'language': lang,
                    'stars': repo.get('stargazers_count', 0),
                    'url': repo.get('html_url')
                })

        return {
            'status': 'success',
            'username': user_data.get('login'),
            'name': user_data.get('name') or user_data.get('login'),
            'bio': user_data.get('bio') or '',
            'public_repos': user_data.get('public_repos', 0),
            'total_stars_in_top_repos': total_stars,
            'top_languages': sorted(list(languages_detected)),
            'skills_topics': sorted(list(topics_detected)),
            'repos': repo_summaries[:5],
            'avatar_url': user_data.get('avatar_url', ''),
        }

    except requests.exceptions.Timeout:
        logger.warning(f"GitHub API timed out after {GITHUB_TIMEOUT_SECONDS}s for user '{clean_username}'.")
        return {
            'status': 'timeout',
            'message': 'GitHub service request timed out after 5 seconds. Upstream API may be sluggish.',
            'username': clean_username
        }
    except requests.exceptions.RequestException as e:
        logger.warning(f"GitHub API connection failure for '{clean_username}': {e}")
        return {
            'status': 'unavailable',
            'message': 'GitHub insights service is currently unreachable.',
            'username': clean_username
        }
