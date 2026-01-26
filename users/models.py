import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# Create your models here.

# If you want to store extra information about users (e.g., bio, phone number, profile picture, preferences),
# you need to create your own model — usually called Profile — and link it to the User model.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    # Add more if needed, e.g., child_age for speech therapy app.

# models.OneToOneField → creates a 1:1 relationship between Profile and User.
# Each user can have at most one profile.
# Each profile belongs to exactly one user.
# if the User is deleted, the related Profile is automatically deleted too.


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # auto_now_add value is set only when the object is first saved, and never updated afterward
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

# We override the default save() method so we can automatically set expires_at if it wasn't already set.
    def save(self, *args, **kwargs):
        # check if is still empty (None)
        # This protects us in case someone manually sets an expiration date
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
# Calls the original Model.save() method to actually save the object to the database
# *args, **kwargs → passes all arguments forward (important for compatibility)
        super().save(*args, **kwargs)
# Convenience method to check if the token can still be used

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Token for {self.user.username}"
