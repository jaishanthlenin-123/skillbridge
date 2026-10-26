from .models import Roadmap, RoadmapItem, RoadmapPriority
from .catalog import get_resources_for_skill
from apps.matches.models import MatchResult

def generate_roadmap_for_match(match: MatchResult) -> Roadmap:
    """
    Constructs a prioritized learning roadmap based on unevidenced skills in the match.
    """
    roadmap = Roadmap.objects.create(
        owner=match.owner,
        match=match,
        title=f"Learning Roadmap: {match.job.title}",
        target_role=match.job.title
    )

    # Missing and Needs Review items
    unmatched_skills = match.skill_results.filter(status__in=['MISSING', 'NEEDS_REVIEW', 'RELATED'])
    
    order = 0
    for item in unmatched_skills:
        skill_name = item.skill_name
        is_mandatory = item.is_mandatory
        status = item.status

        # Prioritization algorithm
        if is_mandatory and status == 'MISSING':
            priority = RoadmapPriority.HIGH
            weeks = 3
            rationale = f"Core mandatory requirement for '{match.job.title}' with no supporting evidence found in resume."
        elif is_mandatory and status in ('RELATED', 'NEEDS_REVIEW'):
            priority = RoadmapPriority.HIGH
            weeks = 2
            rationale = f"Core requirement with partial or adjacent evidence. Formalizing hands-on mastery is strongly recommended."
        elif not is_mandatory and status == 'MISSING':
            priority = RoadmapPriority.MEDIUM
            weeks = 2
            rationale = f"Preferred / nice-to-have qualification that will set your application apart from candidates."
        else:
            priority = RoadmapPriority.LOW
            weeks = 1
            rationale = f"Complementary technology that reinforces existing strengths."

        catalog_data = get_resources_for_skill(skill_name)

        RoadmapItem.objects.create(
            roadmap=roadmap,
            skill_name=skill_name,
            priority=priority,
            estimated_weeks=weeks,
            rationale=rationale,
            suggested_project=catalog_data['project'],
            resources=catalog_data['resources'],
            order_index=order
        )
        order += 1

    return roadmap
