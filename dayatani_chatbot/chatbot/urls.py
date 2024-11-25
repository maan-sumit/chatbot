from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter()
router.register('conversation', ConversationViewSet)
router.register('chat', ChatViewSet)
router.register('feedback', FeedbackViewSet)
router.register('files', FileUploadViewSet)
router.register('train', TrainModelViewSet)
router.register('webhook', WebHookViewset, basename='webhook')
router.register('logs', LogsViewSet)
router.register('batch', BatchStatusViewSet)
router.register('whatsapp', WhatsappModelViewSet, basename='whatsapp')
router.register('questions', QuestionViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
