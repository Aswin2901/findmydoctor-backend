from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from datetime import datetime
from accounts.models import Notification
from appointments.models import Appointment
from geopy.distance import geodesic
from .serializers import (
                          DoctorSignupSerializer ,
                          DoctorLoginSerializer ,
                          DoctorSerializer , 
                          VerificationSerializer,
                          DoctorReviewSerializer ,
                          GetDoctorSerializer,
                          AppointmentAvailabilitySerializer,
                          BreakTimeSerializer,
                          LeaveSerializer ,
                          NotificationSerializer)
from .models import Doctor , Verification , AppointmentAvailability , BreakTime , Leave
from django.http import JsonResponse
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .utils import generate_time_slots, is_time_in_range
from operator import itemgetter



@api_view(['POST'])
def doctor_signup(request):
    print(request.data)
    serializer = DoctorSignupSerializer(data=request.data)
    print(serializer.is_valid() , 'serializer')
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Doctor registered successfully!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def doctor_login(request):
    print(request.data)
    serializer = DoctorLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        doctor = serializer.validated_data
        # Login success; return success response
        return Response({"message": "Login successful", "doctor_id": doctor.id}, status=status.HTTP_200_OK)
    else:
        # Print or log validation errors to debug
        print(serializer.errors)  # This will print errors in your console/log
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

@api_view(['GET'])
def recent_doctors(request):
    doctors = Doctor.objects.order_by('-created_at')[:3]
    serializer = DoctorSerializer(doctors, many=True)
    return Response(serializer.data)

def get_all_doctors(request):
    doctors = Doctor.objects.all().values('id', 'full_name', 'email', 'phone', 'gender','is_verified', 'date_of_birth', 'state', 'address', 'profile_picture')
    return JsonResponse(list(doctors), safe=False)


@api_view(['GET'])
def doctor_verification_status(request, doctor_id):
    print(doctor_id)
    try:
        verification = Doctor.objects.get(id=doctor_id)
        response_data = {
            'is_verified': verification.is_verified,
            'form_submitted': verification.form_submitted
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except Doctor.DoesNotExist:
        return Response({"error": "Doctor verification status not found"}, status=status.HTTP_404_NOT_FOUND)
    
    
@api_view(['POST'])
def doctor_verification(request, doctor_id):
    try:
        # Fetch the doctor instance
        doctor = Doctor.objects.get(id=doctor_id)

        # Log request data and files for debugging
        print("Request Data:", request.data)
        print("Request FILES:", request.FILES)

        # Extract latitude, longitude, and clinic address from the request
        clinic_address = request.data.get('clinic_address')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        print(clinic_address , latitude , longitude)

        # Create verification instance
        verification = Verification.objects.create(
            doctor=doctor,
            qualification=request.data.get('qualification'),
            specialty=request.data.get('specialty'),
            experience=request.data.get('experience'),
            hospital=request.data.get('hospital'),
            clinic_address=clinic_address,
            latitude=latitude,
            longitude=longitude,
            license=request.data.get('license'),
            issuing_authority=request.data.get('issuing_authority'),
            expiry_date=request.data.get('expiry_date'),
            medical_registration=request.data.get('medical_registration'),
            id_proof=request.FILES.get('idProof'),
            medical_license=request.FILES.get('medicalLicense'),
            degree_certificate=request.FILES.get('degreeCertificate'),
        )

        # Mark the doctor form as submitted
        doctor.form_submitted = True
        doctor.save()

        return Response({'message': 'Verification submitted successfully'}, status=status.HTTP_201_CREATED)

    except Doctor.DoesNotExist:
        return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
class DoctorVerificationDetailView(APIView):    
    def get(self, request, doctor_id):
        try:
            verification = Verification.objects.get(doctor__id=doctor_id)
            doctor = Doctor.objects.get(id=doctor_id)
            serializer = DoctorReviewSerializer(verification)
            print('serialiser' ,serializer.data)
            response_data = {
                'doc_id': doctor.id,
                'full_name': doctor.full_name,
                'email': doctor.email,
                'phone': doctor.phone,
                'state': doctor.state,
                'address': doctor.address,
                'date_of_birth':doctor.date_of_birth,
                'gender': doctor.gender, 
                **serializer.data  # Includes serialized verification fields
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Verification.DoesNotExist:
            return Response({"error": "Doctor verification details not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def VerifyDoctor(request, doctor_id):
    try:
        print(f'Received request to verify doctor with ID: {doctor_id}')
        
        doctor = Doctor.objects.get(id=doctor_id)
        print(doctor)
        doctor.is_verified = True
        doctor.save()
        
        return Response(
            {"message": "Doctor verified successfully."},
            status=status.HTTP_200_OK
        )
    
    except Doctor.DoesNotExist:
        print('Doctor not found.')
        return Response(
            {"error": "Doctor not found."},
            status=status.HTTP_404_NOT_FOUND
        )
        
@api_view(['GET'])
def get_verified_doctors(request):
    verified_doctors = Doctor.objects.filter(is_verified=True)
    serializer = GetDoctorSerializer(verified_doctors, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
def mark_availability(request):
    try:
        data = JSONParser().parse(request)
        user_id = data.get('userId')
        date = data.get('date')
        duration = data.get('duration')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        breaks = data.get('breaks', [])

        # Validate inputs
        if not user_id or not date or not start_time or not end_time:
            raise ValueError("Missing required fields: userId, date, start_time, or end_time.")
        if not isinstance(date, str) or not isinstance(start_time, str) or not isinstance(end_time, str):
            raise ValueError("Date, start_time, and end_time must be strings.")

        # Parse date and time fields
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        parsed_start_time = datetime.strptime(start_time, "%I:%M %p").time()
        parsed_end_time = datetime.strptime(end_time, "%I:%M %p").time()
        
        
        print('duration' , duration)
        print("Parsed date:", parsed_date)
        print("Parsed start time:", parsed_start_time)
        print("Parsed end time:", parsed_end_time)
        

        # Validate break times
        parsed_breaks = []
        for break_time in breaks:
            break_start = datetime.strptime(break_time['start'], "%I:%M %p").time()
            break_end = datetime.strptime(break_time['end'], "%I:%M %p").time()
            parsed_breaks.append({'start': break_start, 'end': break_end})

        # Get doctor instance
        doctor = Doctor.objects.get(id=user_id)

        # Save availability
        availability = AppointmentAvailability.objects.create(
            doctor=doctor,
            date=parsed_date,
            duration=duration,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
        )

        print("Parsed breaks:", parsed_breaks)
        
        # Save break times
        for break_time in parsed_breaks:
            BreakTime.objects.create(
                availability=availability,
                start_time=break_time['start'],
                end_time=break_time['end']
            )

        return JsonResponse({'message': 'Availability marked successfully!'}, status=201)

    except ValueError as ve:
        print(f"ValueError: {ve}")
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        print(f"Exception: {e}")
        return JsonResponse({'error': str(e)}, status=400)

class LeaveView(APIView):
    def post(self, request):
        doctor = get_object_or_404(Doctor, email=request.data.get('email'))
        data = {
            "doctor": doctor.id,
            "date": request.data.get("date"),
        }
        serializer = LeaveSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BreakTimeView(APIView):
    def post(self, request):
        availability = get_object_or_404(AppointmentAvailability, id=request.data.get('availability_id'))
        data = {
            "availability": availability.id,
            "start_time": request.data.get("start_time"),
            "end_time": request.data.get("end_time"),
        }
        serializer = BreakTimeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_available_slots(request):
    # Get query parameters
    doctor_id = request.query_params.get('doctorId')
    date = request.query_params.get('date')
    
    # Check if doctorId and date are provided
    if not doctor_id or not date:
        return JsonResponse({'error': 'doctorId and date are required.'}, status=400)

    try:
        # Parse the date
        date = datetime.strptime(date, "%Y-%m-%d").date()

        
        # Fetch the doctor's availability for the date
        availability = AppointmentAvailability.objects.filter(doctor=doctor_id, date=date).first()


        if not availability:
            
            return JsonResponse({'available_slots': [], 'message': 'No availability for the selected date.'}, status=200)

        # Generate all potential slots
        all_slots = generate_time_slots(
            availability.start_time,
            availability.end_time,
            availability.duration
        )
        
        # Fetch break times for the availability
        break_times = BreakTime.objects.filter(availability=availability)
        booked_appointments = Appointment.objects.filter(doctor_id=doctor_id, date=date)
        
        
        # Filter out breaks and booked slots
        available_slots = []
        for slot in all_slots:
            slot_time = datetime.strptime(slot, "%H:%M").time()
            in_break = any(is_time_in_range(break_time.start_time, break_time.end_time, slot_time)
                           for break_time in break_times)
            is_booked = booked_appointments.filter(time=slot_time).exists()

            if not in_break and not is_booked:
                available_slots.append(slot)

        return JsonResponse({'available_slots': available_slots}, status=200)

    except ValueError as e:
        return JsonResponse({'error': 'Invalid date format. Expected format: YYYY-MM-DD'}, status=400)
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(['GET'])
def get_notifications(request, doctor_id):
    notifications = Notification.objects.filter(doctor_id=doctor_id).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['PATCH'])
def mark_notification_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.doctor_is_read = True
        notification.save()
        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)
    except Notification.DoesNotExist:
        print('does not exist')
        return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class DoctorProfileView(APIView):
    def get(self, request, doctor_id):
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            serializer = DoctorSerializer(doctor)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, doctor_id):
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            serializer = DoctorSerializer(doctor, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        


@api_view(['GET'])
def get_nearest_doctors(request):
    try:
        latitude = float(request.GET.get('latitude'))
        longitude = float(request.GET.get('longitude'))
    except ValueError:
        return Response({'error': 'Invalid latitude or longitude'}, status=400)

    user_location = (latitude, longitude)
    verified_doctors = Doctor.objects.filter(is_verified=True)
    serializer = GetDoctorSerializer(verified_doctors, many=True)
    nearest_doctors = []

    for doctor_data in serializer.data:
        print(doctor_data )
        if 'latitude' in doctor_data and 'longitude' in doctor_data and doctor_data['latitude'] and doctor_data['longitude']:
            print('sdhfjhadfhjadhfjkhdjkfhjk')
            doctor_location = (doctor_data['latitude'], doctor_data['longitude'])
            distance = geodesic(user_location, doctor_location).km
            print(distance)
            if distance <= 500:  # Adjust distance threshold as needed
                doctor_data['distance'] = round(distance, 2)
                nearest_doctors.append(doctor_data)
                print('hiiiiii')
    nearest_doctors = sorted(nearest_doctors, key=lambda doctor: doctor['distance'])
    
    print(nearest_doctors)

    return Response(nearest_doctors, status=200)