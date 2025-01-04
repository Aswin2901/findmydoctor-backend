from django.urls import path
from .consumers import PersonalChatConsumer

from appointments.consumers import NotificationConsumer

websocket_urlpatterns = [
    path("ws/chat/<int:id>/", PersonalChatConsumer.as_asgi()),
    path("ws/notifications/<int:user_id>/", NotificationConsumer.as_asgi()),

]
