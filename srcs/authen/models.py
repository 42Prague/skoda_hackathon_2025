from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
import os


# ---------------------
# USER & ACCOUNT
# ---------------------

class User(AbstractUser):

    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(max_length=90, unique=True)
    is_organizer = models.BooleanField(default=True)
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


# ---------------------
# MEMBER (Merged Skills + Learning Fields)
# ---------------------

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Account, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    target_role = models.CharField(max_length=100, blank=False)
    

    def __str__(self):
        return f"{self.user.username} ({self.primary_skill})"


class Roadmap(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name="roadmap")
    svg_path = models.CharField(max_length=255)
    generated_at = models.DateTimeField(auto_now_add=True)
    llm_model_used = models.CharField(max_length=100, blank=True)
    json_data = models.JSONField(default=dict, null=False, blank=False)

    def __str__(self):
        return f"Roadmap for {self.member.user.username}"

    def delete(self, *args, **kwargs):
        """Ensure that the SVG file is also deleted from disk."""
        if self.svg_path and os.path.exists(self.svg_path):
            os.remove(self.svg_path)
        super().delete(*args, **kwargs)

def post_user_created_signal(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance)

post_save.connect(post_user_created_signal, sender=User)


