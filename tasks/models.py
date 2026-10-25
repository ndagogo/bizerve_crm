from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

class Task(models.Model):
    TASK_TYPES = (
        ('passport_renewal', 'International Passport Renewal'),
        ('name_change', 'Change of Name'),
        ('birth_certificate', 'Birth Certificate Request'),
        ('document_verification', 'Document Verification'),
        ('other', 'Other Service'),
    )
    
    STATUS_CHOICES = (
        ('pending', '🟡 Pending Acceptance'),
        ('accepted', '🔵 Accepted'),
        ('processing', '🟠 Processing'),
        ('completed', '🟢 Completed'),
        ('approved', '✅ Approved'),
        ('queried', '❌ Queried'),
        ('declined', '🔴 Declined'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    title = models.CharField(max_length=200)
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    description = models.TextField()
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='assigned_tasks')
    expected_completion = models.DateTimeField()
    actual_completion = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    query_reason = models.TextField(blank=True, null=True)
    decline_reason = models.TextField(blank=True, null=True)  # Add this line
    
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    queried_at = models.DateTimeField(null=True, blank=True)  # Add this line
    
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def get_absolute_url(self):
        return reverse('tasks:task_detail', kwargs={'task_id': self.id})
    
    def get_status_color(self):
        status_colors = {
            'pending': 'warning',
            'accepted': 'info',
            'processing': 'primary',
            'completed': 'success',
            'approved': 'success',
            'queried': 'danger',
            'declined': 'dark',
        }
        return status_colors.get(self.status, 'secondary')
    
    def is_overdue(self):
        if self.expected_completion and timezone.now() > self.expected_completion:
            return self.status not in ['completed', 'approved']
        return False
    
    def can_accept(self):
        return self.status == 'pending' and self.assigned_to != self.created_by

    def can_decline(self):
        return self.status == 'pending' and self.assigned_to != self.created_by
    
    def can_complete(self):
        return self.status in ['accepted', 'processing']
    
    def can_approve(self):
        return self.status == 'completed' and self.created_by != self.assigned_to
    
     

class TaskDocument(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='task_documents/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    document_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_final = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.document_type} - {self.task.title}"

class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_system_note = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"