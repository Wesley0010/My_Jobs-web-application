from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. USER DATABASE (Admin, Applicants, Recruiters)
class User(AbstractUser):
    # Django's AbstractUser gives us username, email, password, first_name, last_name automatically.
    # We just need to add the extra fields from your document.
    
    ROLE_CHOICES = (
        ('APPLICANT', 'Applicant'),
        ('RECRUITER', 'Recruiter'),
        ('ADMIN', 'Admin'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='APPLICANT')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


# 2. RESUME & VACANCY DATABASE
class Resume(models.Model):
    # Links the resume to a specific Applicant
    applicant = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resume')
    file = models.FileField(upload_to='resumes/') # Stores the PDF/DOCX
    parsed_text = models.TextField(blank=True, null=True) # Where we will save extracted text
    extracted_skills = models.TextField(blank=True, null=True) # Where we save AI skills
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume of {self.applicant.username}"

class Job(models.Model):
    # Links the job to the Recruiter who posted it
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='jobs/', blank=True, null=True) # If they upload a doc instead of typing
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# 3. MATCHING DATABASE (Scores and AI results)
class MatchResult(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='matches')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_matches')
    score = models.FloatField() # E.g., 85.5
    feedback = models.TextField(blank=True, null=True) # AI feedback
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title} : {self.score}%"


# 4. APPLICATION & INTERVIEW DATABASE
class Application(models.Model):
    STATUS_CHOICES = (
        ('APPLIED', 'Applied'),
        ('INTERVIEW_SCHEDULED', 'Interview Scheduled'),
        ('REJECTED', 'Rejected'),
        ('HIRED', 'Hired'),
    )
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='APPLIED')
    interview_date = models.DateTimeField(blank=True, null=True) # For recruiters to set
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # An applicant can only apply to a specific job once
        unique_together = ('job', 'applicant')

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title} ({self.status})"


# 5. COMPLAINTS DATABASE
class Complaint(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('RESOLVED', 'Resolved'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    message = models.TextField()
    admin_reply = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint by {self.user.username} - {self.status}"