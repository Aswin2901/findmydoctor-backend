from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from accounts.models import  User
from doctors.models import Doctor
from django.utils.timezone import now , make_aware
from .models import Appointment , Notification
from .serializers import AppointmentSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse
from datetime import datetime


@api_view(['POST'])
def create_appointment(request):
    serializer = AppointmentSerializer(data=request.data)
    if serializer.is_valid():
        appointment = serializer.save()

        # Create notification for the patient
        Notification.objects.create(
            group_name=f"notifications_{appointment.patient.id}",
            patient_message=f"Appointment created successfully on {appointment.date} at {appointment.time}. Please be ready for it.",
            doctor_message=None,
            type="new appointment",
            is_read=False
        )

        # Create notification for the doctor
        Notification.objects.create(
            group_name=f"notifications_{appointment.doctor.id}",
            patient_message=None,
            doctor_message=f"{appointment.patient.full_name} has booked an appointment on {appointment.date} at {appointment.time}.",
            type="new appointment",
            is_read=False
        )

        # Send real-time notifications
        channel_layer = get_channel_layer()

        # Notify patient
        async_to_sync(channel_layer.group_send)(
            f"notifications_{appointment.patient.id}",
            {
                "type": "send_notification",
                "notification": {
                    "group_name": f"notifications_{appointment.patient.id}",
                    "patient_message": f"Appointment created successfully on {appointment.date} at {appointment.time}. Please be ready for it.",
                    "type": "new appointment",
                    "is_read": False,
                    "created_at": appointment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
        )

        # Notify doctor
        async_to_sync(channel_layer.group_send)(
            f"notifications_{appointment.doctor.id}",
            {
                "type": "send_notification",
                "notification": {
                    "group_name": f"notifications_{appointment.doctor.id}",
                    "doctor_message": f"{appointment.patient.full_name} has booked an appointment on {appointment.date} at {appointment.time}.",
                    "type": "new appointment",
                    "is_read": False,
                    "created_at": appointment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def appointment_history(request, doctor_id):
    try:
        appointments = Appointment.objects.filter(doctor_id=doctor_id).order_by('-date', '-time')
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['POST'])
def cancel_appointment(request, appointment_id):
    try:
        # Fetch the appointment
        appointment = Appointment.objects.get(id=appointment_id)

        if appointment.status == 'canceled':
            return Response({'message': 'Appointment is already canceled.'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the appointment status
        appointment.status = 'canceled'
        appointment.save()

        # Create a notification for the patient
        Notification.objects.create(
            group_name=f"notifications_{appointment.patient.id}",
            patient_message=f"Your appointment with Dr. {appointment.doctor.full_name} on {appointment.date} at {appointment.time} has been canceled.",
            doctor_message=None,
            type="appointment cancellation",
            is_read=False
        )

        # Create a notification for the doctor
        Notification.objects.create(
            group_name=f"notifications_{appointment.doctor.id}",
            patient_message=None,
            doctor_message=f"Appointment with {appointment.patient.full_name} on {appointment.date} at {appointment.time} was canceled.",
            type="appointment cancellation",
            is_read=False
        )

        # Send real-time notifications
        channel_layer = get_channel_layer()

        # Notify patient
        async_to_sync(channel_layer.group_send)(
            f"notifications_{appointment.patient.id}",
            {
                "type": "send_notification",
                "notification": {
                    "group_name": f"notifications_{appointment.patient.id}",
                    "patient_message": f"Your appointment with Dr. {appointment.doctor.full_name} on {appointment.date} at {appointment.time} has been canceled.",
                    "type": "appointment cancellation",
                    "is_read": False,
                },
            },
        )

        # Notify doctor
        async_to_sync(channel_layer.group_send)(
            f"notifications_{appointment.doctor.id}",
            {
                "type": "send_notification",
                "notification": {
                    "group_name": f"notifications_{appointment.doctor.id}",
                    "doctor_message": f"Appointment with {appointment.patient.full_name} on {appointment.date} at {appointment.time} was canceled.",
                    "type": "appointment cancellation",
                    "is_read": False,
                },
            },
        )

        return Response({'message': 'Appointment canceled successfully.'}, status=status.HTTP_200_OK)

    except Appointment.DoesNotExist:
        return Response({'error': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def patients_of_doctor(request, doctor_id):
    try:
        # Ensure the doctor exists
        doctor = Doctor.objects.get(id=doctor_id)

        # Get distinct patients who have appointments with the doctor
        patient_ids = Appointment.objects.filter(doctor=doctor).values_list('patient', flat=True).distinct()
        patients = User.objects.filter(id__in=patient_ids)

        # Serialize the patients' data
        patient_data = [{'id': patient.id, 'full_name': patient.full_name, 'email': patient.email} for patient in patients]
        
        return Response(patient_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def doctors_of_patient(request, user_id):
    try:
        # Ensure the patient exists
        patient = User.objects.get(id=user_id)

        # Get distinct doctors who have appointments with the patient
        doctor_ids = Appointment.objects.filter(patient=patient).values_list('doctor', flat=True).distinct()
        doctors = Doctor.objects.filter(id__in=doctor_ids)

        # Serialize the doctors' data
        doctor_data = [{'id': doctor.id, 'full_name': doctor.full_name, 'email': doctor.email} for doctor in doctors]

        return Response(doctor_data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['PATCH'])
def mark_notification_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
def get_dashboard_counts(request):
    total_doctors = Doctor.objects.count()
    total_users = User.objects.count()
    total_appointments = Appointment.objects.count()
    new_appointments = Appointment.objects.filter(status='new').count()  # Adjust the status condition as per your model
    return JsonResponse({
        "total_doctors": total_doctors,
        "total_users": total_users,
        "total_appointments": total_appointments,
        "new_appointments": new_appointments,
    })

@api_view(['GET'])
def get_appointments(request):
    appointments = Appointment.objects.all().values(
        'id', 'doctor__full_name', 'patient__full_name', 'date', 'time', 'status'
    )
    
    return JsonResponse(list(appointments), safe=False)



@api_view(['GET'])
def get_all_appointment(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    current_time = now()
    
    
    all_appointments = Appointment.objects.filter(
        patient=user 
    )
    
    for appointment in all_appointments:
        appointment_datetime = datetime.combine(appointment.date, appointment.time)
        # Convert it to timezone-aware
        appointment_datetime = make_aware(appointment_datetime)

        if appointment.status not in ['completed', 'canceled'] and appointment_datetime < current_time:
            appointment.status = 'completed'
            appointment.save()

    # Manually serialize data
    def format_appointment(appointment):
        print(appointment)
        return {
            "id": appointment.id,
            "doctor_name": appointment.doctor.full_name,
            "doctor_id": appointment.doctor.id,
            "date": appointment.date.strftime('%Y-%m-%d'),
            "time": appointment.time.strftime('%H:%M:%S'),
            "status": appointment.status,
            "reason_for_visit": appointment.reason_for_visit,
        }

    data = {
        "appointments": [format_appointment(app) for app in all_appointments]
    }
    
    return JsonResponse(data, status=200)

@api_view(['POST'])
def user_cancel_appointment(request, appointment_id , user_id):
    try:
        user =  User.objects.get(id=user_id)
        appointment = Appointment.objects.get(id=appointment_id, patient=user)
        if appointment.status in ['pending', 'Confirmed']:
            appointment.status = 'canceled'
            appointment.save()
            
            Notification.objects.create(
                group_name=f"notifications_{appointment.patient.id}",
                patient_message=f"Your appointment with Dr. {appointment.doctor.full_name} on {appointment.date} at {appointment.time} has been canceled.",
                doctor_message=None,
                type="appointment cancellation",
                is_read=False
            )

            # Create a notification for the doctor
            Notification.objects.create(
                group_name=f"notifications_{appointment.doctor.id}",
                patient_message=None,
                doctor_message=f"Appointment with {appointment.patient.full_name} on {appointment.date} at {appointment.time} was canceled.",
                type="appointment cancellation",
                is_read=False
            )

            # Send real-time notifications
            channel_layer = get_channel_layer()

            # Notify patient
            async_to_sync(channel_layer.group_send)(
                f"notifications_{appointment.patient.id}",
                {
                    "type": "send_notification",
                    "notification": {
                        "group_name": f"notifications_{appointment.patient.id}",
                        "patient_message": f"Your appointment with Dr. {appointment.doctor.full_name} on {appointment.date} at {appointment.time} has been canceled.",
                        "type": "appointment cancellation",
                        "is_read": False,
                    },
                },
            )

            # Notify doctor
            async_to_sync(channel_layer.group_send)(
                f"notifications_{appointment.doctor.id}",
                {
                    "type": "send_notification",
                    "notification": {
                        "group_name": f"notifications_{appointment.doctor.id}",
                        "doctor_message": f"Appointment with {appointment.patient.full_name} on {appointment.date} at {appointment.time} was canceled.",
                        "type": "appointment cancellation",
                        "is_read": False,
                    },
                },
            )
            return Response({"message": "Appointment canceled successfully"}, status=200)
        return Response({"error": "Cannot cancel this appointment"}, status=400)
    except Appointment.DoesNotExist:
        return Response({"error": "Appointment not found"}, status=404)