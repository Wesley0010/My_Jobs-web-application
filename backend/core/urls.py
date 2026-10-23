from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('upload-resume/', views.upload_resume, name='upload_resume'), # <-- Add
    path('create-job/', views.create_job, name='create_job'),          # <-- Add
    path('recruiter-jobs/', views.get_recruiter_jobs, name='recruiter_jobs'),
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('chat/', views.chat_with_ai, name='chat'),
    path('apply/<int:job_id>/', views.apply_for_job, name='apply_for_job'),
    path('job/<int:job_id>/applications/', views.get_job_applications, name='get_job_applications'),
    path('schedule-interview/<int:application_id>/', views.schedule_interview, name='schedule_interview'),
    path('admin-data/', views.get_admin_data, name='admin_data'),
    path('admin-update-role/<int:user_id>/', views.update_user_role, name='update_user_role'),
]
