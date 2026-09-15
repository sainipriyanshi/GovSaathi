from django.db import models

# Create your models here.
class Scheme(models.Model):
    name = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    full_description = models.TextField()
    ministry = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    eligibility = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    application_process = models.TextField(blank=True)
    official_url = models.URLField(blank=True)
    language = models.CharField(max_length=50, default="en")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaxDocument(models.Model):
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    content = models.TextField()
    financial_year = models.CharField(max_length=20, blank=True)
    language = models.CharField(max_length=50, default="en")
    source_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
 

class ChatSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    user_identifier = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)
    detected_language = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or self.session_id

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    citations = models.JSONField(default=list, blank=True)
    detected_language = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role} message - {self.session.session_id}"