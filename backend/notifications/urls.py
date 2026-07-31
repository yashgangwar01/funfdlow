from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, UnreadCountView

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('unread-count/', UnreadCountView.as_view(), name='unread_notifications_count'),
    path('', include(router.urls)),
]
