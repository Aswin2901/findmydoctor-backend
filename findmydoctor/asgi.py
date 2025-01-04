import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findmydoctor.settings')

# Initialize Django's ASGI application early to populate the app registry
django_asgi_app = get_asgi_application()

# Defer these imports until after the app registry is ready
from chat.route import websocket_urlpatterns
from chat.channels_middleware import JWTWebsocketMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTWebsocketMiddleware(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
