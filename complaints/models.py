from django.db import models
from django.contrib.auth.models import User
import uuid

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('reopened', 'Reopened'),
    ]
    
    URGENCY_CHOICES = [
        ('Normal', 'Normal'),
        ('High', 'High'),
    ]
    
    # Basic Info
    complaint_id = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    
    # Complaint Details
    complaint_type = models.CharField(max_length=200, default='General')
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='Normal')
    location = models.CharField(max_length=255, default='Not specified')
    details = models.TextField()
    
    # Personal Info
    name = models.CharField(max_length=100)
    roll = models.CharField(max_length=50, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # GPS Location
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    gps_accuracy = models.FloatField(null=True, blank=True)
    
    # Feedback
    feedback = models.TextField(blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    feedback_submitted_at = models.DateTimeField(blank=True, null=True)
    
    # Reopen Info
    reopened = models.BooleanField(default=False)
    reopen_reason = models.TextField(blank=True, null=True)
    reopen_count = models.IntegerField(default=0)
    
    # Reminder
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.complaint_id:
            # Generate CMP + random 8 digits
            self.complaint_id = f"CMP{str(uuid.uuid4().int)[:8]}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.complaint_id} - {self.user.username} - {self.status}"

class ComplaintFile(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='complaint_files/%Y/%m/%d/')
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, null=True, blank=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"