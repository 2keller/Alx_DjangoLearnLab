# feelings/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(max_length=500, blank=True, help_text="Tell us about yourself")
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_absolute_url(self):
        return reverse('feelings:profile', kwargs={'username': self.user.username})

    @property
    def total_hugs_received(self):
        return sum(post.hugs for post in self.user.posts.all())

    @property
    def total_tears_received(self):
        return sum(post.tears for post in self.user.posts.all())

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    hugs = models.PositiveIntegerField(default=0)
    tears = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']  # newest first

    def __str__(self):
        return f"{self.user.username}: {self.content[:40]}"

class Reaction(models.Model):
    REACTION_CHOICES = [
        ('hug', '🤗'),
        ('tear', '😢'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reactions")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")
    reaction_type = models.CharField(max_length=4, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post', 'reaction_type']  # One reaction per user per post per type

    def __str__(self):
        return f"{self.user.username} {self.get_reaction_type_display()} {self.post.id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on Post {self.post_id}"
# ifeel_mini/settings.py