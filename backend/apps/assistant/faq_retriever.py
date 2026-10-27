import re
from typing import List, Dict, Any
from django.db.models import Q
from apps.faq.models import FAQ

def retrieve_relevant_faqs(query: str, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Retrieves the most relevant active FAQ records from PostgreSQL
    using lexical token scoring and phrase matching.
    """
    clean_query = query.strip().lower()
    if not clean_query:
        return []

    # Tokenize query words (length > 2)
    tokens = [t for t in re.findall(r'\b\w+\b', clean_query) if len(t) > 2]
    
    # Query database
    all_faqs = list(FAQ.objects.filter(is_active=True).select_related('category'))
    if not all_faqs:
        return []

    scored_faqs = []
    for faq in all_faqs:
        score = 0.0
        q_lower = faq.question.lower()
        a_lower = faq.answer.lower()

        # Exact phrase match in question gets massive boost
        if clean_query in q_lower:
            score += 10.0
        
        # Token matches
        for t in tokens:
            if t in q_lower:
                score += 3.0
            if t in a_lower:
                score += 1.0

        if score > 0:
            scored_faqs.append((score, faq))

    scored_faqs.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, faq in scored_faqs[:limit]:
        results.append({
            'id': str(faq.id),
            'question': faq.question,
            'answer': faq.answer,
            'category': faq.category.name if faq.category else 'General',
            'relevance_score': score,
        })

    return results
