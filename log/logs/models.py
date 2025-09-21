from django.db import models
from django.contrib.auth.models import User

class LogEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_log_entries')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10)
    star_trek_quote = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"[{self.user.username}] [{self.timestamp}] {self.level}: {self.star_trek_quote}"