from rest_framework import serializers
from .models import Doctor , Verification , AppointmentAvailability , Leave , BreakTime
from django.contrib.auth.hashers import make_password , check_password
from rest_framework import serializers
from accounts.models import Notification
from django.core.files.uploadedfile import InMemoryUploadedFile



class DoctorSignupSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Doctor
        fields = ['full_name', 'email', 'phone', 'gender', 'date_of_birth', 'state', 'address', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])  # Hash the password
        validated_data.pop('confirm_password')  # Remove confirm_password before saving
        doctor = Doctor.objects.create(**validated_data)
        print('doctor' , doctor)
        return doctor




class DoctorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        print(email , password)

        try:
            # Check if the doctor exists
            doctor = Doctor.objects.get(email=email)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Doctor with this email does not exist.")

        # Check if the password is correct
        if not check_password(password, doctor.password):
            raise serializers.ValidationError("Incorrect password.")

        # Return the validated doctor data if everything is correct
        return doctor


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            'id', 'full_name', 'email', 'phone', 'gender', 
            'date_of_birth', 'state', 'address', 'profile_picture', 'is_verified'
        ]

    def update(self, instance, validated_data):
        # Remove `profile_picture` if it's not a valid file
        profile_picture = validated_data.get('profile_picture', None)
        if profile_picture and not isinstance(profile_picture, InMemoryUploadedFile):
            validated_data.pop('profile_picture', None)
        
        return super().update(instance, validated_data)
        

class VerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = [
            'doctor',
            'id_proof',
            'medical_license',
            'degree_certificate',
            'license_number',
            'issuing_authority',
            'license_expiry_date',
            'medical_registration',
            'verification_date',
        ]
        extra_kwargs = {
            'doctor': {'required': True},
        }

    def create(self, validated_data):
        verification = Verification.objects.create(**validated_data)
        return verification
    
class DoctorReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = '__all__'  
        
class GetDoctorSerializer(serializers.ModelSerializer):
    qualification = serializers.CharField(source='verification.qualification', read_only=True)
    specialty = serializers.CharField(source='verification.specialty', read_only=True)
    experience = serializers.IntegerField(source='verification.experience', read_only=True)
    hospital = serializers.CharField(source='verification.hospital', read_only=True)
    clinic_address = serializers.CharField(source='verification.clinic_address', read_only=True)
    latitude = serializers.FloatField(source='verification.latitude' , read_only = True)
    longitude = serializers.FloatField(source='verification.longitude' , read_only = True)

    class Meta:
        model = Doctor
        fields = [
            'id', 'full_name', 'email', 'phone', 'gender', 'profile_picture', 
            'qualification', 'specialty', 'experience', 'hospital', 'clinic_address' , 'latitude' ,
            'longitude'
        ]
        
class AppointmentAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentAvailability
        fields = '__all__'

class LeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = '__all__'

class BreakTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakTime
        fields = '__all__'
        
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'doctor', 'type', 'message', 'doctor_message', 'doctor_is_read', 'is_read', 'created_at']