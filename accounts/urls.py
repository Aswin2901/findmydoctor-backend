from django.urls import path
from .views import register_user ,verify_otp , CustomTokenObtainPairView , GoogleCallbackView , google_login , all_users
from . import views

urlpatterns = [
    path('register/', register_user, name='register_user'),  
    path('verify-otp/', verify_otp, name='verify_otp'), 
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('oauth/login/', google_login , name='google_login'),
    path('oauth/callback/', GoogleCallbackView.as_view(), name='google_callback'),
    path('all/' , all_users , name='all_users'),
    path('get_profile/<int:userId>/', views.get_user_profile, name='get_user_profile'),
    path('add-to-my-doctors/', views.add_to_my_doctors, name='add-to-my-doctors'),
    path('<int:user_id>/favorites/', views.user_favorite_doctors, name='user_favorite_doctors'),
    path('remove_fav/<int:fav_id>/', views.remove_favorite_doctor , name='remove_fevorate'),
    path('create-notification/', views.create_notification, name='create_notification'),
    path('get-notification/<int:user_id>/', views.get_notifications, name='get_notifications'),
    path('mark-as-read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('update_user_profile/<int:user_id>/', views.update_user_profile, name='update_user_profile'),
    path('<int:user_id>/block/', views.BlockUserView.as_view(), name='block-user'),
]
