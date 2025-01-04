from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_appointment, name='create_appointment'),
    path('history/<int:doctor_id>/', views.appointment_history, name='appointment_history'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('doctors/<int:doctor_id>/patients/', views.patients_of_doctor, name='patients_of_doctor'),
    path('patients/<int:user_id>/doctors/' , views.doctors_of_patient , name='doctors_of_patient'),
    path('notifications/<int:notification_id>/mark-as-read/', views.mark_notification_as_read, name='mark-as-read'),
    path('dashboard/counts/', views.get_dashboard_counts, name='dashboard-counts'),
    path('all_appointments/', views.get_appointments, name='appointments'),
    path('get_appointments/<int:user_id>/', views.get_all_appointment, name='appointment-list'),
    path('<int:appointment_id>/user_cancel/<int:user_id>', views.user_cancel_appointment, name='user-cancel-appointment'),
]