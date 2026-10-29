from django.urls import path
from . import views

urlpatterns = [
    # --- AUTHENTICATION ---
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    
    # --- APPLICANT & RECRUITER UPLOADS ---
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    path('create-job/', views.create_job, name='create_job'),
    path('recruiter-jobs/', views.get_recruiter_jobs, name='recruiter_jobs'),
    
    # --- AI MATCHING ---
    path('matched-jobs/', views.get_matched_jobs, name='matched_jobs'),
    path('job/<int:job_id>/applicants/', views.get_applicants_for_job, name='job_applicants'),
    
    # --- PROFILE SETTINGS ---
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # --- CHATBOT ---
    path('chat/', views.chat_with_ai, name='chat'),
    
    # --- APPLICATIONS & INTERVIEWS ---
    path('apply/<int:job_id>/', views.apply_for_job, name='apply_for_job'),
    path('job/<int:job_id>/applications/', views.get_job_applications, name='get_job_applications'),
    path('schedule-interview/<int:application_id>/', views.schedule_interview, name='schedule_interview'),
    path('report/<int:job_id>/', views.download_report, name='download_report'),
    
    # --- ADMIN ---
    path('admin-data/', views.get_admin_data, name='admin_data'),
    path('admin-update-role/<int:user_id>/', views.update_user_role, name='update_user_role'),
    
    # settings
    path('browse-jobs/', views.browse_all_jobs, name='browse_jobs'),
    path('my-applications/', views.get_my_applications, name='my_applications'),
    path('complaints/', views.create_complaint, name='create_complaint'),
    path('complaints/my/', views.get_my_complaints, name='my_complaints'),
    path('complaints/all/', views.get_all_complaints, name='all_complaints'),
    path('complaints/reply/<int:complaint_id>/', views.reply_complaint, name='reply_complaint'),
    path('interview-letter/<int:application_id>/', views.generate_interview_letter, name='interview_letter'),
    path('recruiter-logs/', views.get_recruiter_logs, name='recruiter_logs'),
]