from django.urls import path
from .views import ( doctor_signup ,
                    doctor_login ,
                    recent_doctors ,
                    get_all_doctors ,
                    doctor_verification_status ,
                    doctor_verification ,
                    DoctorVerificationDetailView ,
                    VerifyDoctor , get_verified_doctors,
                    mark_availability,
                    LeaveView,
                    BreakTimeView, 
                    get_available_slots,
                    get_notifications,
                    mark_notification_as_read,
                    DoctorProfileView,
                    get_nearest_doctors
                    
                    
)
urlpatterns = [
    path('register/', doctor_signup, name='doctor-signup'),
    path('login/', doctor_login, name='doctor-login'),
    path('recent/', recent_doctors, name='recent_doctors'),
    path('all/', get_all_doctors, name='get_all_doctors'),
    path('verification/<int:doctor_id>/', doctor_verification_status, name='doctor_verification_status'),
    path('verify/<int:doctor_id>/', doctor_verification, name='doctor-verification'),
    path('review/<int:doctor_id>/', DoctorVerificationDetailView.as_view(), name='doctor-verification-detail'),
    path('makeverify/<int:doctor_id>/', VerifyDoctor, name='verify-doctor'),
    path('getdoctors/', get_verified_doctors , name='get_verified_doctors' ),
    path('availability/', mark_availability, name='appointment-availability'),
    path('leave/', LeaveView.as_view(), name='leave'),
    path('break-time/', BreakTimeView.as_view(), name='break-time'),
    path('availability/slots/', get_available_slots, name='get_available_slots'),
    path('get-notifications/<int:doctor_id>/' ,get_notifications , name='get_notification' ),
    path('mark-as-read/<int:notification_id>/', mark_notification_as_read  , name='mark-as-read'),
    path('profile/<int:doctor_id>/', DoctorProfileView.as_view(), name='doctor_profile'),
    path('nearest/', get_nearest_doctors, name='get_nearest_doctors'),
    
]
