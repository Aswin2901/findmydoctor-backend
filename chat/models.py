from django.db import models
from accounts.models import User
from doctors.models import Doctor
from appointments.models import Appointment
from django.utils.timezone import now

class ChatMessage(models.Model):
    group_name = models.TextField(null=False ,default=None)
    message = models.TextField()
    sender = models.TextField(default='' , null=True)
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"
