from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class JWTAuthentication(BaseJWTAuthentication):
    def authenticate_websocket(self, scope, token):
        validated_token = self.get_validated_token(token)
        user = self.get_user(validated_token)
        if user is None:
            raise AuthenticationFailed("User not found")

        return user
