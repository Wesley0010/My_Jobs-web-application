import os
import google.generativeai as genai
from dotenv import load_dotenv
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime
from django.core.mail import send_mail
from django.contrib.auth import authenticate

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

from .models import User, Resume, Job, MatchResult, Application
from .serializers import UserRegistrationSerializer
from .utils import extract_text_from_file, calculate_match_score
from .models import User, Resume, Job, MatchResult, Application, Complaint

# Load Gemini API Key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ==========================================
# 1. AUTHENTICATION
# ==========================================
@api_view(['POST'])
def register_user(request):
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "User registered successfully",
                "token": token.key,
                "user_id": user.id,
                "role": user.role
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful",
                "token": token.key,
                "user_id": user.id,
                "role": user.role,
                "first_name": user.first_name,  # <--- ADDED THIS
                "last_name": user.last_name     # <---
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

# ==========================================
# 2. UPLOADS & JOBS
# ==========================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_resume(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        resume, created = Resume.objects.update_or_create(
            applicant=request.user,
            defaults={'file': file}
        )

        extracted_text = extract_text_from_file(resume.file.path)
        resume.parsed_text = extracted_text
        resume.save()

        return Response({
            "message": "Resume uploaded and parsed successfully!",
            "text_preview": extracted_text[:200]
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job(request):
    if request.user.role != 'RECRUITER':
        return Response({"error": "Only recruiters can post jobs"}, status=status.HTTP_403_FORBIDDEN)

    title = request.data.get('title')
    description = request.data.get('description')
    file = request.FILES.get('file')

    if not title or not description:
        return Response({"error": "Title and description are required"}, status=status.HTTP_400_BAD_REQUEST)

    job = Job.objects.create(
        recruiter=request.user,
        title=title,
        description=description,
        file=file
    )

    if file:
        extracted_text = extract_text_from_file(job.file.path)
        job.description += f"\n\n--- Extracted from Document ---\n{extracted_text}"
        job.save()

    return Response({"message": "Job posted successfully!", "job_id": job.id}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recruiter_jobs(request):
    if request.user.role != 'RECRUITER':
        return Response({"error": "Only recruiters can access this"}, status=status.HTTP_403_FORBIDDEN)
    
    jobs = Job.objects.filter(recruiter=request.user).order_by('-posted_at')
    job_list = [{"id": j.id, "title": j.title, "description": j.description, "posted_at": j.posted_at} for j in jobs]
    return Response(job_list, status=status.HTTP_200_OK)

# ==========================================
# 3. AI MATCHING
# ==========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_matched_jobs(request):
    if request.user.role != 'APPLICANT':
        return Response({"error": "Only applicants can access this"}, status=status.HTTP_403_FORBIDDEN)

    try:
        resume = Resume.objects.get(applicant=request.user)
        if not resume.parsed_text:
            return Response({"error": "Resume text is empty. Please upload a valid document."}, status=status.HTTP_400_BAD_REQUEST)
    except Resume.DoesNotExist:
        return Response({"error": "Please upload a resume first"}, status=status.HTTP_400_BAD_REQUEST)

    jobs = Job.objects.all()
    matched_jobs = []

    for job in jobs:
        job_text = f"{job.title} {job.description}"
        score = calculate_match_score(resume.parsed_text, job_text)

        if score > 10.0:
            MatchResult.objects.update_or_create(
                job=job, applicant=request.user,
                defaults={'score': score}
            )
            matched_jobs.append({
                "job_id": job.id,
                "title": job.title,
                "description": job.description,
                "recruiter": job.recruiter.username,
                "score": score
            })

    matched_jobs = sorted(matched_jobs, key=lambda x: x['score'], reverse=True)
    return Response(matched_jobs, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_applicants_for_job(request, job_id):
    if request.user.role != 'RECRUITER':
        return Response({"error": "Only recruiters can access this"}, status=status.HTTP_403_FORBIDDEN)

    try:
        job = Job.objects.get(id=job_id, recruiter=request.user)
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    job_text = f"{job.title} {job.description}"
    resumes = Resume.objects.exclude(parsed_text__isnull=True).exclude(parsed_text="")
    matched_applicants = []

    for resume in resumes:
        score = calculate_match_score(resume.parsed_text, job_text)
        if score > 10.0:
            MatchResult.objects.update_or_create(
                job=job, applicant=resume.applicant,
                defaults={'score': score}
            )
            matched_applicants.append({
                "applicant_id": resume.applicant.id,
                "name": f"{resume.applicant.first_name} {resume.applicant.last_name}",
                "email": resume.applicant.email,
                "score": score
            })

    matched_applicants = sorted(matched_applicants, key=lambda x: x['score'], reverse=True)
    return Response(matched_applicants, status=status.HTTP_200_OK)

# ==========================================
# 4. PROFILE & SETTINGS
# ==========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    user = request.user
    return Response({
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "date_of_birth": user.date_of_birth,
        "role": user.role
    }, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    data = request.data

    user.first_name = data.get('first_name', user.first_name)
    user.middle_name = data.get('middle_name', user.middle_name)
    user.last_name = data.get('last_name', user.last_name)
    user.email = data.get('email', user.email)
    user.phone_number = data.get('phone_number', user.phone_number)
    
    if 'date_of_birth' in data:
        user.date_of_birth = data['date_of_birth'] if data['date_of_birth'] else None

    new_username = data.get('username')
    if new_username and new_username != user.username:
        if User.objects.filter(username=new_username).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)
        user.username = new_username

    try:
        user.save()
        return Response({"message": "Profile updated successfully!"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ==========================================
# 5. CHATBOT
# ==========================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_ai(request):
    user_message = request.data.get('message')
    if not user_message:
        return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"You are a helpful career assistant for a job matching website called My_Jobs. The user is a {request.user.role}. Answer this: {user_message}"
        response = model.generate_content(prompt)
        return Response({"reply": response.text}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==========================================
# 6. APPLICATIONS & INTERVIEWS
# ==========================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_for_job(request, job_id):
    if request.user.role != 'APPLICANT':
        return Response({"error": "Only applicants can apply"}, status=status.HTTP_403_FORBIDDEN)
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    if Application.objects.filter(job=job, applicant=request.user).exists():
        return Response({"error": "You have already applied for this job"}, status=status.HTTP_400_BAD_REQUEST)

    Application.objects.create(job=job, applicant=request.user)
    return Response({"message": "Application submitted successfully!"}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_applications(request, job_id):
    if request.user.role != 'RECRUITER':
        return Response({"error": "Only recruiters can view applications"}, status=status.HTTP_403_FORBIDDEN)
    try:
        job = Job.objects.get(id=job_id, recruiter=request.user)
    except Job.DoesNotExist:
        return Response({"error": "Job not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)

    applications = Application.objects.filter(job=job).order_by('-applied_at')
    data = [{
        "application_id": app.id,
        "applicant_name": f"{app.applicant.first_name} {app.applicant.last_name}",
        "email": app.applicant.email,
        "status": app.status,
        "interview_date": app.interview_date
    } for app in applications]
    return Response(data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def schedule_interview(request, application_id):
    if request.user.role != 'RECRUITER':
        return Response({"error": "Only recruiters can schedule interviews"}, status=status.HTTP_403_FORBIDDEN)
    try:
        application = Application.objects.get(id=application_id, job__recruiter=request.user)
    except Application.DoesNotExist:
        return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

    date_str = request.data.get('interview_date')
    if not date_str:
        return Response({"error": "Interview date is required"}, status=status.HTTP_400_BAD_REQUEST)

    application.interview_date = parse_datetime(date_str)
    application.status = 'INTERVIEW_SCHEDULED'
    application.save()

    subject = f"Interview Invitation: {application.job.title}"
    message = f"Dear {application.applicant.first_name},\n\nYou have been invited for an interview for {application.job.title}.\n\nDate & Time: {application.interview_date}\n\nBest regards,\n{request.user.first_name}"
    send_mail(subject, message, 'noreply@myjobs.com', [application.applicant.email], fail_silently=False)

    return Response({"message": "Interview scheduled and email sent!"}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_report(request, job_id):
    if request.user.role != 'RECRUITER':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try:
        job = Job.objects.get(id=job_id, recruiter=request.user)
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    applications = Application.objects.filter(job=job)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Report_{job.title}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Applicant Report: {job.title}")
    
    p.setFont("Helvetica", 12)
    y = 700
    if not applications:
        p.drawString(100, y, "No applications received yet.")
    else:
        for app in applications:
            p.drawString(100, y, f"Name: {app.applicant.first_name} {app.applicant.last_name}")
            p.drawString(100, y - 15, f"Email: {app.applicant.email}")
            p.drawString(100, y - 30, f"Status: {app.status}")
            y -= 60
            if y < 50:
                p.showPage()
                y = 750

    p.showPage()
    p.save()
    return response

# ==========================================
# 7. ADMIN
# ==========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_admin_data(request):
    if request.user.role != 'ADMIN':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    users = User.objects.all().values('id', 'username', 'email', 'first_name', 'last_name', 'role')
    jobs = Job.objects.all().values('id', 'title', 'description', 'recruiter__username')
    return Response({"users": list(users), "jobs": list(jobs)}, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_role(request, user_id):
    if request.user.role != 'ADMIN':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try:
        user_to_update = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    new_role = request.data.get('role')
    if new_role not in ['APPLICANT', 'RECRUITER', 'ADMIN']:
        return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

    user_to_update.role = new_role
    user_to_update.save()
    return Response({"message": f"User {user_to_update.username} updated to {new_role}"}, status=status.HTTP_200_OK)

# --- BROWSE ALL JOBS (APPLICANT) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def browse_all_jobs(request):
    if request.user.role != 'APPLICANT':
        return Response({"error": "Only applicants can browse jobs"}, status=status.HTTP_403_FORBIDDEN)
    jobs = Job.objects.all().order_by('-posted_at')
    data = [{
        "id": job.id, "title": job.title, "description": job.description, 
        "recruiter": job.recruiter.username, "posted_at": job.posted_at
    } for job in jobs]
    return Response(data, status=status.HTTP_200_OK)

# --- GET MY APPLICATIONS (APPLICANT LOGS) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_applications(request):
    if request.user.role != 'APPLICANT':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    apps = Application.objects.filter(applicant=request.user).order_by('-applied_at')
    data = [{
        "application_id": app.id, "job_title": app.job.title, "status": app.status,
        "interview_date": app.interview_date, "applied_at": app.applied_at
    } for app in apps]
    return Response(data, status=status.HTTP_200_OK)

# --- COMPLAINTS / REPORTS ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_complaint(request):
    message = request.data.get('message')
    if not message:
        return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)
    Complaint.objects.create(user=request.user, message=message)
    return Response({"message": "Complaint submitted to Admin"}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_complaints(request):
    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')
    data = [{"id": c.id, "message": c.message, "reply": c.admin_reply, "status": c.status, "date": c.created_at} for c in complaints]
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_complaints(request):
    if request.user.role != 'ADMIN':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    complaints = Complaint.objects.all().order_by('-created_at')
    data = [{"id": c.id, "user": c.user.username, "role": c.user.role, "message": c.message, "reply": c.admin_reply, "status": c.status, "date": c.created_at} for c in complaints]
    return Response(data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reply_complaint(request, complaint_id):
    if request.user.role != 'ADMIN':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try:
        complaint = Complaint.objects.get(id=complaint_id)
    except Complaint.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    
    reply = request.data.get('reply')
    if not reply:
        return Response({"error": "Reply required"}, status=status.HTTP_400_BAD_REQUEST)
    
    complaint.admin_reply = reply
    complaint.status = 'RESOLVED'
    complaint.save()
    return Response({"message": "Reply sent"}, status=status.HTTP_200_OK)

# --- INTERVIEW LETTER GENERATION (APPLICANT) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_interview_letter(request, application_id):
    if request.user.role != 'APPLICANT':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try:
        app = Application.objects.get(id=application_id, applicant=request.user)
        if app.status != 'INTERVIEW_SCHEDULED':
            return Response({"error": "Interview not scheduled yet"}, status=status.HTTP_400_BAD_REQUEST)
    except Application.DoesNotExist:
        return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Interview_Letter_{app.job.title}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(150, 750, "MY_JOBS INTERVIEW INVITATION")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 680, f"Date: {app.interview_date.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(100, 650, f"Dear {app.applicant.first_name} {app.applicant.last_name},")
    p.drawString(100, 620, f"We are pleased to invite you for an interview for the position of:")
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 600, f"{app.job.title}")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 550, f"Recruiter: {app.job.recruiter.first_name} {app.job.recruiter.last_name}")
    p.drawString(100, 520, "Please ensure you arrive 10 minutes before your scheduled time.")
    p.drawString(100, 480, "We look forward to meeting you!")
    
    p.showPage()
    p.save()
    return response

# --- RECRUITER LOGS ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recruiter_logs(request):
    if request.user.role != 'RECRUITER':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    
    jobs = Job.objects.filter(recruiter=request.user).order_by('-posted_at')
    logs = []
    
    for job in jobs:
        applications = Application.objects.filter(job=job)
        logs.append({
            "job_id": job.id,
            "title": job.title,
            "posted_at": job.posted_at,
            "total_applicants": applications.count(),
            "interviews_scheduled": applications.filter(status='INTERVIEW_SCHEDULED').count(),
            "applicants": [{
                "name": f"{app.applicant.first_name} {app.applicant.last_name}",
                "status": app.status,
                "date": app.interview_date
            } for app in applications]
        })
        
    return Response(logs, status=status.HTTP_200_OK)