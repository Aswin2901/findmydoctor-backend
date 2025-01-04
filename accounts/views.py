from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer , AllUserSerializer , NotificationSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny ,IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
import random
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.core.cache import cache
from social_django.utils import psa
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
import requests
import os
from dotenv import load_dotenv
load_dotenv()
from .models import User , MyDoctor
from appointments.models import Notification
from doctors.models import Doctor
from doctors.serializers import DoctorSerializer
from rest_framework.decorators import api_view, permission_classes
import json
from rest_framework_simplejwt.tokens import RefreshToken




def generate_otp():
    return random.randint(100000, 999999)


def send_otp_email(email, otp):
    send_mail(
        'Your OTP Code',
        f'Your OTP is {otp}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )



@csrf_exempt
@api_view(['POST'])
def register_user(request):
    email = request.data.get('email')


    otp = generate_otp()
    cache.set(email, otp, timeout=300) 
    print(f"OTP cached for {email}: {otp}") 

    # Send OTP to email
    send_otp_email(email, otp)

    return JsonResponse({'message': 'OTP sent to your email'}, status=status.HTTP_200_OK)


# Verify OTP and register the user if OTP is valid
@csrf_exempt
@api_view(['POST'])
def verify_otp(request):
    email = request.data.get('email')
    input_otp = request.data.get('otp')
    cached_otp = cache.get(email)


    if cached_otp and str(cached_otp) == input_otp:
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        else:
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)


# Custom JWT Token Obtain View
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed as e:
            return Response({'error': str(e)}, status=400)
        
        Response = ({
            'access': response.data['access'],
            'refresh': response.data['refresh'],
            'user': {
                'email': request.data['email'],
                'phone': request.data.get('phone'),
                'gender': request.data.get('gender'),
            }
        })
        print(Response)

        return Response



# Function to initiate Google OAuth login
@api_view(['GET'])
def google_login(request):
    redirect_uri = os.getenv('OAUTH_CALLBACK', 'http://localhost:3000/oauth/callback/')
    auth_url = (
        'https://accounts.google.com/o/oauth2/auth'
        f'?response_type=code&client_id={settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY}'
        f'&redirect_uri={redirect_uri}'
        '&scope=email profile'
        '&access_type=offline'
        '&prompt=consent'
    )
    return Response({'auth_url': auth_url})


class GoogleCallbackView(APIView):
    def get(self, request, *args, **kwargs):
        code = request.GET.get('code')

        if not code:
            return Response({'error': 'Authorization code not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            flow = Flow.from_client_secrets_file(
                os.getenv('path_to_client_secret_json'),  # Preferably use settings for sensitive paths
                scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
                redirect_uri='http://localhost:3000/oauth/callback/'
            )
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            access_token = credentials.token
            refresh_token = credentials.refresh_token

            # Check if refresh_token is None and handle it
            if refresh_token is None:
                return Response({'error': 'Refresh token was not provided. Re-authentication may be required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Get user info from Google
            user_info_endpoint = 'https://www.googleapis.com/oauth2/v2/userinfo'
            response = requests.get(user_info_endpoint, headers={'Authorization': f'Bearer {access_token}'})
            user_info = response.json()

            email = user_info['email']
            full_name = user_info.get('name', '')
            gender = user_info.get('gender', 'Not specified')

            # Check if the user already exists
            try:
                user = User.objects.get(email=email)
                refresh = RefreshToken.for_user(user) 
                is_doctor = hasattr(user, 'doctor')  # Check if the user is also a doctor
            except User.DoesNotExist:
                user = User.objects.create(
                    email=email,
                    full_name=full_name,
                )
                user.set_unusable_password()
                user.save()
                is_doctor = False
                refresh = RefreshToken.for_user(user) 

            # Prepare the response data
            response_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'is_doctor': is_doctor,
                'id': user.id,  # User ID
                'doctor_id': user.doctor.id if is_doctor else None,  # Doctor ID if applicable
                'is_superuser': user.is_superuser,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f"An error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        
@api_view(['GET'])
def all_users(request):
    users = User.objects.all()
    serializer = AllUserSerializer(users, many=True)
    return Response(serializer.data)




@api_view(['GET'])
def get_user_profile(request, userId):
    try:
        # Retrieve the user instance
        user = User.objects.get(id=userId)
        
        # Serialize the user data into a dictionary (or use a serializer if needed)
        user_data = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "gender": user.gender,
            "phone": user.phone,
            "address": user.address,
            "location": user.location,
        }
        
        return Response(user_data)

    except User.DoesNotExist:
        # Return 404 if the user does not exist
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
def add_to_my_doctors(request):
    doctor_id = request.data.get("doctor_id")
    user_id = request.data.get('userId')
    user = User.objects.get(id = user_id)

    try:
        doctor = Doctor.objects.get(id=doctor_id)
        my_doctor, created = MyDoctor.objects.get_or_create(user=user, doctor=doctor)
        if created:
            return Response({"message": "Doctor added to My Doctors"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Doctor already in My Doctors"}, status=status.HTTP_200_OK)
    except Doctor.DoesNotExist:
        return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
def user_favorite_doctors(request, user_id):
    try:
        # Retrieve all favorite doctors for the specified user
        favorite_doctors = MyDoctor.objects.filter(user_id=user_id).select_related('doctor__verification')
        
        # Check if the user has any favorite doctors
        if not favorite_doctors.exists():
            return Response({"error": "No favorite doctors found."}, status=status.HTTP_404_NOT_FOUND)

        # Manually build the response data
        response_data = []
        for fav in favorite_doctors:
            doctor = fav.doctor

            doctor_data = {
                "full_name": doctor.full_name,
                "email": doctor.email,
                "phone": doctor.phone,
                "gender": doctor.gender,
                "created_at": doctor.created_at,
            }

            # Add verification fields if they exist
            if hasattr(doctor, 'verification') and doctor.verification:
                print(doctor.verification.clinic_address)
                doctor_data.update({
                    "id": doctor.verification.id,
                    "qualification": doctor.verification.qualification,
                    "specialty": doctor.verification.specialty,
                    "experience": doctor.verification.experience,
                    "hospital": doctor.verification.hospital,
                    "clinic": doctor.verification.clinic_address,
                    'fav_id' : fav.id,
                })
                
                print(doctor_data)
                

            response_data.append(doctor_data)

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        # Handle any unexpected errors
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['DELETE'])
def remove_favorite_doctor(request, fav_id):
    try:
        fav_doctor = MyDoctor.objects.get(id=fav_id)
        user = fav_doctor.user
        fav_doctor.delete()

        all_doctor = MyDoctor.objects.filter(user_id=user.id).select_related('doctor__verification')
        if not all_doctor.exists():
            return Response({"message": "No favorite doctors found."}, status=status.HTTP_204_NO_CONTENT)

        # Manually build the response data
        response_data = []
        for fav in all_doctor:
            doctor = fav.doctor
            doctor_data = {
                "full_name": doctor.full_name,
                "email": doctor.email,
                "phone": doctor.phone,
                "gender": doctor.gender,
                "created_at": doctor.created_at,
            }

            # Add verification fields if they exist
            if hasattr(doctor, 'verification') and doctor.verification:
                doctor_data.update({
                    "id": doctor.verification.id,
                    "qualification": doctor.verification.qualification,
                    "specialty": doctor.verification.specialty,
                    "experience": doctor.verification.experience,
                    "hospital": doctor.verification.hospital,
                    "clinic": doctor.verification.clinic_address,
                    'fav_id': fav.id,
                })

            response_data.append(doctor_data)

        return Response({"message": "Doctor removed from favorites.", 'data': response_data}, status=status.HTTP_200_OK)

    except Exception as e:
        print("An error occurred:", e)
        return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
    
@api_view(['POST'])
def create_notification(request):
    try:
        user = User.objects.get(id=request.data['user_id'])
        doctor = Doctor.objects.get(id=request.data['doctor_id'])
        notification = Notification.objects.create(
            user=user,
            doctor=doctor,
            notification_type=request.data['notification_type'],
            message=request.data['message']
        )
        return Response({"message": "Notification created successfully."}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_notifications(request, user_id):
    notifications = Notification.objects.filter(user_id=user_id).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['PATCH'])
def mark_notification_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)
    except Notification.DoesNotExist:
        print('does not exist')
        return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['PATCH'])
def update_user_profile(request, user_id):
    try:
        user = User.objects.get(id=user_id)

        user.full_name = request.data.get('full_name', user.full_name)
        user.phone = request.data.get('phone', user.phone)
        user.gender = request.data.get('gender', user.gender)
        user.address = request.data.get('address', user.address )
        
        # Update location-related fields
        user.location = request.data.get('location', user.location)
        user.latitude = request.data.get('latitude', user.latitude)
        user.longitude = request.data.get('longitude', user.longitude)
        
        user.save()

        
        serializer = UserSerializer(user)
        

        return Response({'message': 'Profile updated successfully.', 'user': serializer.data }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    
class BlockUserView(APIView):
    def patch(self, request, user_id):
        user = User.objects.get(id = user_id)
        is_active = request.data.get('is_active', None)
        if is_active is None:
            return Response({"error": "is_active field is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_active = is_active
        user.save()
        return Response({"message": "User status updated.", "is_active": user.is_active}, status=status.HTTP_200_OK)