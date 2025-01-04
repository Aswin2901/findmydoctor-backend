from django.db import models
from django.utils import timezone
from doctors.models import Doctor
from accounts.models import User
from django.utils.timezone import now

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled')
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason_for_visit = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.full_name} on {self.date} at {self.time}"
    

class Notification(models.Model):
    group_name = models.CharField(max_length=255)  # Room/group name for WebSocket
    patient_message = models.TextField(max_length=255, null=True, blank=True)  # Message for the patient
    doctor_message = models.TextField(max_length=255, null=True, blank=True)  # Message for the doctor
    type = models.CharField(max_length=50)  # Notification type (e.g., "new appointment")
    is_read = models.BooleanField(default=False)  # Read status
    created_at = models.DateTimeField(default=now)  # Timestamp of notification creation

    def __str__(self):
        return f"Notification ({self.type}) - Group: {self.group_name}"
