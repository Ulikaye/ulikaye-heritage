from django.db import models
from django.contrib.auth.models import User

class FamilyMember(models.Model):
    full_name = models.CharField(max_length=200)
    birth_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    photo_url = models.URLField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='family_member')

    def __str__(self):
        return self.full_name
    
class ClanStory(models.Model):
    clan_name = models.CharField(max_length=200)
    region = models.CharField(max_length=200, blank=True)
    story = models.TextField()
    key_figure = models.CharField(max_length=200, blank=True)
    year_founded = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.clan_name
    
class ElderVoice(models.Model):
    elder_name = models.CharField(max_length=200)
    year_recorded = models.IntegerField(null=True, blank=True)
    topic = models.CharField(max_length=200, blank=True)
    transcript = models.TextField(blank=True)
    audio_file = models.FileField(upload_to='elders_voices/', blank=True, null=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.elder_name} – {self.topic or 'Voice'}"
    
class TimelineEvent(models.Model):
    EVENT_TYPES = [
        ('Birth', 'Birth'),
        ('Marriage', 'Marriage'),
        ('Migration', 'Migration'),
        ('Graduation', 'Graduation'),
        ('Death', 'Death'),
        ('Other', 'Other'),
    ]
    title = models.CharField(max_length=200)
    year = models.IntegerField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='Other')
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    related_member = models.ForeignKey('FamilyMember', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.year} – {self.title}"
    
class MigrationStory(models.Model):
    title = models.CharField(max_length=200)
    year = models.IntegerField()
    from_place = models.CharField(max_length=200, blank=True)
    to_place = models.CharField(max_length=200, blank=True)
    story = models.TextField(blank=True)
    related_members = models.ManyToManyField('FamilyMember', blank=True, related_name='migrations')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.year} – {self.title}"
    
class Tradition(models.Model):
    CATEGORY_CHOICES = [
        ('Ceremony', 'Ceremony'),
        ('Ritual', 'Ritual'),
        ('Festival', 'Festival'),
        ('Food', 'Food'),
        ('Attire', 'Attire'),
        ('Oral Tradition', 'Oral Tradition'),
        ('Other', 'Other'),
    ]
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    description = models.TextField()
    year_originated = models.IntegerField(null=True, blank=True)
    related_to = models.CharField(max_length=200, blank=True, help_text="Elder name or member ID")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class MediaItem(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('document', 'Document'),
    ]
    title = models.CharField(max_length=200, blank=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='gallery/')
    description = models.TextField(blank=True)
    related_member = models.ForeignKey('FamilyMember', on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"{self.media_type} - {self.uploaded_at}"
    
class InviteCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    used = models.BooleanField(default=False)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_invite')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        if self.used:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user}"