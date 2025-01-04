from django.conf import settings
from accounts.models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from doctors.models import Doctor
import jwt

from rest_framework.exceptions import AuthenticationFailed
from channels.db import database_sync_to_async

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            doctor = Doctor.objects.get(email=email)
            if check_password(password, doctor.password):
                refresh = RefreshToken.for_user(doctor) 
                response_data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'is_doctor': True,
                    'doctor_id': doctor.id,
                    'id': doctor.id,  # Include doctor ID as `id` for consistency
                }
                return Response(response_data, status=status.HTTP_200_OK)
        except Doctor.DoesNotExist:
            pass  
        
        try:
            user_model = get_user_model()
            user = user_model.objects.get(email=email)
            if user.check_password(password):
                response = super().post(request, *args, **kwargs)
                response.data['is_superuser'] = user.is_superuser
                response.data['id'] = user.id  # Include user ID
                response.data['is_doctor'] = False
                return response
        except user_model.DoesNotExist:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)

@database_sync_to_async
def authenticate_websocket(self, scop, token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        self.verify_token(payload=payload)
        
        user_id = payload['id']
        user = User.objects.get(id=user_id)
        return user
    except (User.DoesNotExist):
        raise AuthenticationFailed('Invalid Token')
