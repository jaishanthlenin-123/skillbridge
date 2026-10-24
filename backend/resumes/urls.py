from django.urls import path
from .views import ResumeListCreateView, ResumeDetailView, ResumeSkillsUpdateView, SkillTaxonomyListView

urlpatterns = [
    path('', ResumeListCreateView.as_view(), name='resume-list-create'),
    path('taxonomy/', SkillTaxonomyListView.as_view(), name='skill-taxonomy-list'),
    path('<uuid:pk>/', ResumeDetailView.as_view(), name='resume-detail'),
    path('<uuid:pk>/skills/', ResumeSkillsUpdateView.as_view(), name='resume-skills-update'),
]
