from django.db import models
from django.contrib.auth.models import User

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
