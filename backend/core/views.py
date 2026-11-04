import os
import uuid
from django.conf import settings
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

from .models import User, Resume, Job, MatchResult, Application, Complaint
from .serializers import UserRegistrationSerializer
from .utils import extract_text_from_file, calculate_match_score

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ==========================================
# 1. AUTHENTICATION
# ==========================================
@api_view(['POST'])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.id, "role": user.role}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key, "user_id": user.id, "role": user.role,
            "first_name": user.first_name, "last_name": user.last_name
        }, status=status.HTTP_200_OK)
    return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

# ==========================================
# 2. UPLOADS & JOBS
# ==========================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_resume(request):
    try:
        file = request.FILES.get('file')
        if not file: return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        resume, created = Resume.objects.update_or_create(applicant=request.user, defaults={'file': file})
        resume.parsed_text = extract_text_from_file(resume.file.path)
        resume.save()
        return Response({"message": "Resume uploaded!", "text_preview": resume.parsed_text[:200]}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job(request):
    if request.user.role != 'RECRUITER': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    title = request.data.get('title')
    description = request.data.get('description')
    file = request.FILES.get('file')
    if not title or not description: return Response({"error": "Title and description required"}, status=status.HTTP_400_BAD_REQUEST)

    job = Job.objects.create(recruiter=request.user, title=title, description=description, file=file)
    if file:
        job.description += f"\n\n--- Extracted ---\n{extract_text_from_file(job.file.path)}"
        job.save()
    return Response({"message": "Job posted!", "job_id": job.id}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recruiter_jobs(request):
    if request.user.role != 'RECRUITER': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    jobs = Job.objects.filter(recruiter=request.user).order_by('-posted_at')
    return Response([{"id": j.id, "title": j.title, "description": j.description, "posted_at": j.posted_at} for j in jobs], status=status.HTTP_200_OK)

# ==========================================
# 3. AI MATCHING & SEARCH
# ==========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_matched_jobs(request):
    if request.user.role != 'APPLICANT': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try:
        resume = Resume.objects.get(applicant=request.user)
        if not resume.parsed_text: return Response({"error": "Resume empty"}, status=status.HTTP_400_BAD_REQUEST)
    except Resume.DoesNotExist: return Response({"error": "Upload resume first"}, status=status.HTTP_400_BAD_REQUEST)

    matched_jobs = []
    for job in Job.objects.all():
        score = calculate_match_score(resume.parsed_text, f"{job.title} {job.description}")
        if score > 10.0:
            MatchResult.objects.update_or_create(job=job, applicant=request.user, defaults={'score': score})
            matched_jobs.append({"job_id": job.id, "title": job.title, "description": job.description, "recruiter": job.recruiter.username, "score": score})
    return Response(sorted(matched_jobs, key=lambda x: x['score'], reverse=True), status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_applicants_for_job(request, job_id):
    if request.user.role != 'RECRUITER': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try: job = Job.objects.get(id=job_id, recruiter=request.user)
    except Job.DoesNotExist: return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    matched_applicants = []
    for resume in Resume.objects.exclude(parsed_text__isnull=True).exclude(parsed_text=""):
        score = calculate_match_score(resume.parsed_text, f"{job.title} {job.description}")
        if score > 10.0:
            MatchResult.objects.update_or_create(job=job, applicant=resume.applicant, defaults={'score': score})
            matched_applicants.append({"applicant_id": resume.applicant.id, "name": f"{resume.applicant.first_name} {resume.applicant.last_name}", "email": resume.applicant.email, "score": score})
    return Response(sorted(matched_applicants, key=lambda x: x['score'], reverse=True), status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_applicants(request):
    if request.user.role != 'RECRUITER': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    query = request.GET.get('q', '')
    if not query: return Response([])
    
    results = []
    for resume in Resume.objects.filter(parsed_text__icontains=query):
        text = resume.parsed_text.lower()
        index = text.find(query.lower())
        snippet = resume.parsed_text[max(0, index-50):min(len(text), index+100)] if index != -1 else ""
        results.append({"applicant_id": resume.applicant.id, "name": f"{resume.applicant.first_name} {resume.applicant.last_name}", "email": resume.applicant.email, "snippet": f"...{snippet}..."})
    return Response(results, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_match_resumes(request, job_id):
    if request.user.role != 'RECRUITER': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try: job = Job.objects.get(id=job_id, recruiter=request.user)
    except Job.DoesNotExist: return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    files = request.FILES.getlist('files')
    if not files: return Response({"error": "No files"}, status=status.HTTP_400_BAD_REQUEST)

    job_text = f"{job.title} {job.description}"
    results = []
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_bulk')
    os.makedirs(temp_dir, exist_ok=True)

    for file in files:
        temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.name}")
        try:
            with open(temp_file_path, 'wb+') as dest:
                for chunk in file.chunks(): dest.write(chunk)
            score = calculate_match_score(extract_text_from_file(temp_file_path), job_text)
            results.append({"filename": file.name, "score": score})
        except Exception as e: results.append({"filename": file.name, "score": 0, "error": str(e)})
        finally:
            if os.path.exists(temp_file_path): os.remove(temp_file_path)
    return Response(sorted(results, key=lambda x: x['score'], reverse=True), status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def match_custom_vacancy(request):
    if request.user.role != 'APPLICANT': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try: resume = Resume.objects.get(applicant=request.user)
    except Resume.DoesNotExist: return Response({"error": "Upload resume first"}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES.get('file')
    if not file: return Response({"error": "No file"}, status=status.HTTP_400_BAD_REQUEST)

    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_vacancy')
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.name}")

    try:
        with open(temp_file_path, 'wb+') as dest:
            for chunk in file.chunks(): dest.write(chunk)
        score = calculate_match_score(resume.parsed_text, extract_text_from_file(temp_file_path))
        return Response({"score": score, "filename": file.name}, status=status.HTTP_200_OK)
    finally:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)

# ==========================================
# 4. PROFILE, LOGS & COMPLAINTS
# ==========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    user = request.user
    return Response({"username": user.username, "email": user.email, "first_name": user.first_name, "middle_name": user.middle_name, "last_name": user.last_name, "phone_number": user.phone_number, "date_of_birth": user.date_of_birth, "role": user.role}, status=status.HTTP_200_OK)

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
    if 'date_of_birth' in data: user.date_of_birth = data['date_of_birth'] if data['date_of_birth'] else None
    new_username = data.get('username')
    if new_username and new_username != user.username:
        if User.objects.filter(username=new_username).exists(): return Response({"error": "Username taken"}, status=status.HTTP_400_BAD_REQUEST)
        user.username = new_username
    user.save()
    return Response({"message": "Profile updated!"}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def browse_all_jobs(request):
    if request.user.role != 'APPLICANT': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    jobs = Job.objects.all().order_by('-posted_at')
    return Response([{"id": job.id, "title": job.title, "description": job.description, "recruiter": job.recruiter.username, "posted_at": job.posted_at} for job in jobs], status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_applications(request):
    if request.user.role != 'APPLICANT': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    apps = Application.objects.filter(applicant=request.user).order_by('-applied_at')
    return Response([{"application_id": app.id, "job_title": app.job.title, "status": app.status, "interview_date": app.interview_date, "applied_at": app.applied_at} for app in apps], status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recruiter_logs(request):
    if request.user.role != 'RECRUITER': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    logs = []
    for job in Job.objects.filter(recruiter=request.user).order_by('-posted_at'):
        applications = Application.objects.filter(job=job)
        logs.append({"job_id": job.id, "title": job.title, "posted_at": job.posted_at, "total_applicants": applications.count(), "interviews_scheduled": applications.filter(status='INTERVIEW_SCHEDULED').count(), "applicants": [{"name": f"{app.applicant.first_name} {app.applicant.last_name}", "status": app.status, "date": app.interview_date} for app in applications]})
    return Response(logs, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_complaint(request):
    message = request.data.get('message')
    if not message: return Response({"error": "Message required"}, status=status.HTTP_400_BAD_REQUEST)
    Complaint.objects.create(user=request.user, message=message)
    return Response({"message": "Complaint submitted!"}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_complaints(request):
    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')
    return Response([{"id": c.id, "message": c.message, "reply": c.admin_reply, "status": c.status, "date": c.created_at} for c in complaints], status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_complaints(request):
    if request.user.role != 'ADMIN': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    complaints = Complaint.objects.all().order_by('-created_at')
    return Response([{"id": c.id, "user": c.user.username, "role": c.user.role, "message": c.message, "reply": c.admin_reply, "status": c.status, "date": c.created_at} for c in complaints], status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reply_complaint(request, complaint_id):
    if request.user.role != 'ADMIN': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try: complaint = Complaint.objects.get(id=complaint_id)
    except Complaint.DoesNotExist: return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    reply = request.data.get('reply')
    if not reply: return Response({"error": "Reply required"}, status=status.HTTP_400_BAD_REQUEST)
    complaint.admin_reply = reply
    complaint.status = 'RESOLVED'
    complaint.save()
    return Response({"message": "Reply sent"}, status=status.HTTP_200_OK)

# ==========================================
# 5. CHATBOT
# ==========================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_ai(request):
    user_message = request.data.get('message')
    if not user_message: return Response({"error": "Message required"}, status=status.HTTP_400_BAD_REQUEST)

    context = ""
    if request.user.role == 'APPLICANT':
        try:
            resume = Resume.objects.get(applicant=request.user)
            context += f"\nUser's Resume Summary: {resume.parsed_text[:1000]}"
            matches = MatchResult.objects.filter(applicant=request.user).order_by('-score')[:3]
            if matches: context += f"\nTop Matches: {', '.join([f'{m.job.title} ({m.score}%)' for m in matches])}"
        except Resume.DoesNotExist: context += "\nUser has not uploaded a resume yet."
    elif request.user.role == 'RECRUITER':
        context += f"\nPosted Jobs: {', '.join([j.title for j in Job.objects.filter(recruiter=request.user)])}"

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"You are a career assistant for My_Jobs. User Role: {request.user.role}. Context: {context}. Question: {user_message}. Provide a personalized, helpful answer."
        response = model.generate_content(prompt)
        return Response({"reply": response.text}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"GEMINI ERROR: {str(e)}")
        return Response({"reply": "I'm having trouble connecting right now. Please check the Django terminal."}, status=status.HTTP_200_OK)

# ==========================================
# 6. APPLICATIONS & INTERVIEWS
# ==========================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_for_job(request, job_id):
    if request.user.role != 'APPLICANT': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try: job = Job.objects.get(id=job_id)
    except Job.DoesNotExist: return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
    if Application.objects.filter(job=job, applicant=request.user).exists(): return Response({"error": "Already applied"}, status=status.HTTP_400_BAD_REQUEST)
    Application.objects.create(job=job, applicant=request.user)
    return Response({"message": "Application submitted!"}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_applications(request, job_id):
    if request.user.role != 'RECRUITER': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try: job = Job.objects.get(id=job_id, recruiter=request.user)
    except Job.DoesNotExist: return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
    apps = Application.objects.filter(job=job).order_by('-applied_at')
    return Response([{"application_id": app.id, "applicant_name": f"{app.applicant.first_name} {app.applicant.last_name}", "email": app.applicant.email, "status": app.status, "interview_date": app.interview_date} for app in apps], status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def schedule_interview(request, application_id):
    if request.user.role != 'RECRUITER': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try: application = Application.objects.get(id=application_id, job__recruiter=request.user)
    except Application.DoesNotExist: return Response({"error": "App not found"}, status=status.HTTP_404_NOT_FOUND)
    date_str = request.data.get('interview_date')
    if not date_str: return Response({"error": "Date required"}, status=status.HTTP_400_BAD_REQUEST)
    application.interview_date = parse_datetime(date_str)
    application.status = 'INTERVIEW_SCHEDULED'
    application.save()
    try:
        send_mail(f"Interview: {application.job.title}", f"Dear {application.applicant.first_name},\n\nInterview Date: {application.interview_date}", 'noreply@myjobs.com', [application.applicant.email], fail_silently=False)
        email_status = "Email sent."
    except Exception as e:
        print(f"Email failed: {e}")
        email_status = "Email failed."
    return Response({"message": f"Interview scheduled! {email_status}"}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_report(request, job_id):
    if request.user.role != 'RECRUITER': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try: job = Job.objects.get(id=job_id, recruiter=request.user)
    except Job.DoesNotExist: return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Report_{job.title}.pdf"'
    p = canvas.Canvas(response, pagesize=letter)
    p.setFont("Helvetica-Bold", 16); p.drawString(100, 750, f"Applicant Report: {job.title}")
    y = 700
    for app in Application.objects.filter(job=job):
        p.drawString(100, y, f"Name: {app.applicant.first_name} {app.applicant.last_name} | Status: {app.status}")
        y -= 30
    p.save()
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_interview_letter(request, application_id):
    if request.user.role != 'APPLICANT': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try: app = Application.objects.get(id=application_id, applicant=request.user)
    except Application.DoesNotExist: return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    if app.status != 'INTERVIEW_SCHEDULED': return Response({"error": "Not scheduled"}, status=status.HTTP_400_BAD_REQUEST)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Interview_Letter.pdf"'
    p = canvas.Canvas(response, pagesize=letter)
    p.setFont("Helvetica-Bold", 20); p.drawString(150, 750, "INTERVIEW INVITATION")
    p.setFont("Helvetica", 12); p.drawString(100, 680, f"Dear {app.applicant.first_name}, you are invited for {app.job.title} on {app.interview_date}.")
    p.save()
    return response

# ==========================================
# 7. ADMIN
# ==========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_admin_data(request):
    if request.user.role != 'ADMIN': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    return Response({
        "users": list(User.objects.all().values('id', 'username', 'email', 'first_name', 'last_name', 'role')),
        "jobs": list(Job.objects.all().values('id', 'title', 'description', 'recruiter__username')),
        "stats": {"total_users": User.objects.count(), "total_jobs": Job.objects.count(), "total_resumes": Resume.objects.count()},
        "resumes": list(Resume.objects.all().values('id', 'applicant__username', 'parsed_text'))
    }, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_role(request, user_id):
    if request.user.role != 'ADMIN': return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    try: user = User.objects.get(id=user_id)
    except User.DoesNotExist: return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    new_role = request.data.get('role')
    if new_role not in ['APPLICANT', 'RECRUITER', 'ADMIN']: return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)
    user.role = new_role; user.save()
    return Response({"message": "Role updated"}, status=status.HTTP_200_OK)