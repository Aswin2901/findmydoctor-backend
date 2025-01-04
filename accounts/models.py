from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from doctors.models import Doctor
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15 , null=True)
    gender = models.CharField(max_length=10 , null=True)
    date_of_birth = models.DateField(null=True)
    state = models.CharField(max_length=50 , null=True)
    address = models.TextField(null=True)
    
    location = models.TextField(blank=True, null=True)  # New field
    latitude = models.FloatField(blank=True, null=True)  # New field
    longitude = models.FloatField(blank=True, null=True)

    # Add these fields for permissions
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone', 'gender', 'date_of_birth', 'state', 'address']

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True  # Allow all permissions for simplicity; implement logic as needed.

    def has_perms(self, perms, obj=None):
        "Does the user have a specific set of permissions?"
        return all(self.has_perm(perm, obj) for perm in perms)

    def has_module_perms(self, app_label):
        "Does the user have permission to view the app 'app_label'?"
        return True  # Allow all modules for simplicity; implement logic as needed.


class MyDoctor(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_doctors")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="saved_by_users")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'doctor')  # Prevents duplicate entries

    def __str__(self):
        return f"{self.user.full_name} - {self.doctor.full_name}"
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    type = models.CharField(max_length=50 , null=True) 
    message = models.TextField(max_length=255 , null=True)
    doctor_message = models.TextField(max_length=255)
    is_read = models.BooleanField(default=False)
    doctor_is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notification for {self.user.full_name} - {self.type}"