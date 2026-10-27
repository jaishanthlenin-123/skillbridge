from django.urls import path
from .views import FAQListView, FAQCategoryListView

urlpatterns = [
    path('', FAQListView.as_view(), name='faq-list'),
    path('categories/', FAQCategoryListView.as_view(), name='faq-category-list'),
]
