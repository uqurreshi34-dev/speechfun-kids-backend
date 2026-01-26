from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Letter(models.Model):
    letter = models.CharField(max_length=1, unique=True)

    def __str__(self):
        return self.letter.upper()   # or just return self.letter


class Word(models.Model):
    word = models.CharField(max_length=50)
    # cascade: "When the object I'm pointing to gets deleted, automatically delete me too
    # (and anything that depends on me, and so on)."
    # Django automatically deletes all the Words that were pointing to that Letter
    # if The Letter "A" is gone
    # "Apple", "Ant", "Axe", etc. are also gone automatically etc
    letter = models.ForeignKey(Letter, on_delete=models.CASCADE)
    # For speech audio files.
    audio = models.FileField(null=True, blank=True)
    # Django needs two different pieces of information for each option:
    # The real value that gets saved in the database
    # → short, usually lowercase, good for code & storage
    # The nice/human-readable name that users see in forms / admin / dropdowns
    # That's why its written as tuples of 2 items
    difficulty = models.CharField(max_length=10, choices=[(
        'easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')])
# Add this for admin

    def __str__(self):
        return self.word


class Challenge(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=10, choices=[(
        'easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')])
    created_at = models.DateTimeField(auto_now_add=True)  # Added for sorting.
    # Add fields for interactive elements, e.g., quiz questions.

    def __str__(self):
        return f"{self.title or 'Say ' + self.word.word} ({self.difficulty})"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)  # Added for tracking.

    def __str__(self):
        status = "✓" if self.completed else "○"
        return f"{status} {self.user.username} - {self.challenge.title}"
