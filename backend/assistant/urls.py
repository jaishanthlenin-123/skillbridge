from django.urls import path
from .views import ChatAssistantView, ChatFeedbackView

urlpatterns = [
    path('chat/', ChatAssistantView.as_view(), name='assistant-chat'),
    path('feedback/', ChatFeedbackView.as_view(), name='assistant-feedback'),
]
