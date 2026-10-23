from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Resume, Job
from .utils import extract_text_from_file
# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import UserRegistrationSerializer
import os
import google.generativeai as genai
from dotenv import load_dotenv
from .models import Resume, Job, MatchResult, Application
from django.utils.dateparse import parse_datetime
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.core.mail import send_mail


load_dotenv() # Loads the .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 1. SIGNUP API
@api_view(['POST'])
def register_user(request):
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Create a token for the user right after they register
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "User registered successfully",
                "token": token.key,
                "user_id": user.id,
                "role": user.role
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 2. LOGIN API
@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        
        # authenticate() checks the database for the correct username/password
        user = authenticate(username=username, password=password)
        
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful",
                "token": token.key,
                "user_id": user.id,
                "role": user.role
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # --- APPLICANT: UPLOAD RESUME ---
@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Only logged-in users can upload
def upload_resume(request):
    try:
        # Get the file from the request
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Save the file to the Resume model
        # update_or_create ensures if they upload again, it replaces the old one
        resume, created = Resume.objects.update_or_create(
            applicant=request.user,
            defaults={'file': file}
        )

        # 2. Extract text from the saved file
        extracted_text = extract_text_from_file(resume.file.path)
        resume.parsed_text = extracted_text
        resume.save()

        return Response({
            "message": "Resume uploaded and parsed successfully!",
            "text_preview": extracted_text[:200] # Send back first 200 chars for proof
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- RECRUITER: CREATE JOB ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job(request):
    if request.user.role != 'RECRUITER':
        return Response({"error": "Only recruiters can post jobs"}, status=status.HTTP_403_FORBIDDEN)

    title = request.data.get('title')
    description = request.data.get('description')
    file = request.FILES.get('file') # Vacancy file (optional)

    if not title or not description:
        return Response({"error": "Title and description are required"}, status=status.HTTP_400_BAD_REQUEST)

    job = Job.objects.create(
        recruiter=request.user,
        title=title,
        description=description,
        file=file
    )

    # If they uploaded a vacancy document, parse it and append to description
    if file:
        extracted_text = extract_text_from_file(job.file.path)
        job.description += f"\n\n--- Extracted from Document ---\n{extracted_text}"
        job.save()

    return Response({"message": "Job posted successfully!", "job_id": job.id}, status=status.HTTP_201_CREATED)

# --- RECRUITER: GET THEIR OWN POSTED JOBS ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recruiter_jobs(request):
    if request.user.role != 'RECRUITER':
        return Response({"error": "Only recruiters can access this"}, status=status.HTTP_403_FORBIDDEN)

    # Fetch jobs where the recruiter is the currently logged-in user
    jobs = Job.objects.filter(recruiter=request.user).order_by('-posted_at')
    
    job_list = []
    for job in jobs:
        job_list.append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "posted_at": job.posted_at
        })
        
    return Response(job_list, status=status.HTTP_200_OK)

# --- GET USER PROFILE ---
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

# --- UPDATE USER PROFILE ---
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    data = request.data

    # Update the fields. If a field is missing in the request, keep the old one.
    user.first_name = data.get('first_name', user.first_name)
    user.middle_name = data.get('middle_name', user.middle_name)
    user.last_name = data.get('last_name', user.last_name)
    user.email = data.get('email', user.email)
    user.phone_number = data.get('phone_number', user.phone_number)
    
    # Only update DOB if provided
    if 'date_of_birth' in data and data['date_of_birth']:
        user.date_of_birth = data['date_of_birth']

    # Check if they are trying to change their username (must ensure it doesn't already exist)
    new_username = data.get('username')
    if new_username and new_username != user.username:
        if User.objects.filter(username=new_username).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)
        user.username = new_username

    user.save()
    return Response({"message": "Profile updated successfully!"}, status=status.HTTP_200_OK)

# --- AI CHATBOT ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_ai(request):
    user_message = request.data.get('message')
    if not user_message:
        return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Initialize the Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # We give the AI context based on the user's role
        prompt = f"You are a helpful career assistant for a job matching website called My_Jobs. The user is a {request.user.role}. Answer this: {user_message}"
        
        response = model.generate_content(prompt)
        
        return Response({"reply": response.text}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- APPLICANT: APPLY FOR A JOB ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_for_job(request, job_id):
    if request.user.role != 'APPLICANT':
        return Response({"error": "Only applicants can apply"}, status=status.HTTP_403_FORBIDDEN)

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if already applied
    if Application.objects.filter(job=job, applicant=request.user).exists():
        return Response({"error": "You have already applied for this job"}, status=status.HTTP_400_BAD_REQUEST)

    Application.objects.create(job=job, applicant=request.user)
    return Response({"message": "Application submitted successfully!"}, status=status.HTTP_201_CREATED)


# --- RECRUITER: GET ALL APPLICATIONS FOR THEIR JOB ---
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
    
    data = []
    for app in applications:
        data.append({
            "application_id": app.id,
            "applicant_name": f"{app.applicant.first_name} {app.applicant.last_name}",
            "email": app.applicant.email,
            "status": app.status,
            "interview_date": app.interview_date
        })
    return Response(data, status=status.HTTP_200_OK)


# --- RECRUITER: SCHEDULE INTERVIEW ---
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

    # --- SEND EMAIL NOTIFICATION ---
    subject = f"Interview Invitation: {application.job.title}"
    message = f"Dear {application.applicant.first_name},\n\nYou have been invited for an interview for the position of {application.job.title}.\n\nDate & Time: {application.interview_date}\n\nBest regards,\n{request.user.first_name} {request.user.last_name}"
    
    send_mail(
        subject,
        message,
        'noreply@myjobs.com', # From email
        [application.applicant.email], # To email
        fail_silently=False,
    )

    return Response({"message": "Interview scheduled and email sent!"}, status=status.HTTP_200_OK)
# --- ADMIN: GET ALL USERS AND JOBS ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_admin_data(request):
    if request.user.role != 'ADMIN':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    # Fetch all users (excluding passwords for security)
    users = User.objects.all().values('id', 'username', 'email', 'first_name', 'last_name', 'role')
    
    # Fetch all jobs
    jobs = Job.objects.all().values('id', 'title', 'description', 'recruiter__username')

    return Response({
        "users": list(users),
        "jobs": list(jobs)
    }, status=status.HTTP_200_OK)


# --- ADMIN: UPDATE USER ROLE ---
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