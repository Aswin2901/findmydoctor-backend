from django.contrib import admin
from accounts.models import User , MyDoctor , Notification

admin.site.register(User)
admin.site.register(MyDoctor)
admin.site.register(Notification)