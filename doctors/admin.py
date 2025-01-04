from django.contrib import admin
from .models import Doctor , Verification , AppointmentAvailability , BreakTime , Leave

admin.site.register(Doctor)
admin.site.register(Verification)
admin.site.register(AppointmentAvailability)
admin.site.register(BreakTime)
admin.site.register(Leave)




