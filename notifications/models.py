from django.db import models
from django.contrib.auth import get_user_model

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Both'),
    )
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    related_task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}"