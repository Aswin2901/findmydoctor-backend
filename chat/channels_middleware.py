from asgiref.sync import sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework.exceptions import AuthenticationFailed
from django.db import close_old_connections
from accounts.tokenauthentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from doctors.models import Doctor


class JWTWebsocketMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        close_old_connections()

        # Extract token from query string
        query_string = scope.get("query_string", b"").decode("utf-8")

        query_parameters = dict(
            qp.split("=", 1) if "=" in qp else (qp, None) for qp in query_string.split("&")
        )

        token = query_parameters.get("token", None)
        role = query_parameters.get("role", None)
        print('role', role)

        if token is None:
            await send({
                "type": "websocket.close",
                "code": 4000  # Token not provided
            })
            return

        authentication = JWTAuthentication()

        try:
            if role == 'doctor':
                validated_token = AccessToken(token)
                id = validated_token.get("user_id")

                # Use sync_to_async to run the database query in a separate thread
                user = await sync_to_async(self.get_doctor_by_id)(id)
            else:
                user = await sync_to_async(authentication.authenticate_websocket)(scope, token)

            print("Authenticated user:", user)

            if user is not None:
                scope['user'] = user
            else:
                await send({
                    "type": "websocket.close",
                    "code": 4001  # Invalid token
                })
                return

            # Proceed to the next middleware or consumer
            return await super().__call__(scope, receive, send)

        except AuthenticationFailed:
            await send({
                "type": "websocket.close",
                "code": 4002  # Authentication failed
            })

    # Create a synchronous method for the database query
    def get_doctor_by_id(self, id):
        return Doctor.objects.get(id=id)