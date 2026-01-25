# challenges/admin.py
from django.contrib import admin
from .models import Letter, Word, Challenge, Comment, UserProgress


@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    list_display = ('letter',)          # shows in list view
    search_fields = ('letter',)


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('word', 'letter', 'difficulty')
    list_filter = ('difficulty', 'letter')
    search_fields = ('word',)


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'get_letter',           # custom method instead of 'letter'
        'word',                 # show the linked word
        'get_word_audio',
        'difficulty',
        'created_at',
    )
    list_filter = (
        'difficulty',
        'word__letter',         # filter by letter via the word
    )
    search_fields = (
        'title',
        'description',
        'word__word',           # search inside the word name
    )
    date_hierarchy = 'created_at'

    # Custom method to display the letter nicely
    @admin.display(ordering='word__letter__letter', description='Letter')
    def get_letter(self, obj):
        if obj.word and obj.word.letter:
            return obj.word.letter.letter.upper()
        return '-'

    @admin.display(description='Audio')
    def get_word_audio(self, obj):
        if obj.word and obj.word.audio:
            return "Yes (click to play in frontend)"
        return "No audio"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'created_at', 'short_text')
    list_filter = ('challenge', 'created_at')
    search_fields = ('text', 'user__username')
    date_hierarchy = 'created_at'

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Text preview'


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'completed', 'score', 'updated_at')
    list_filter = ('completed', 'challenge__difficulty')
    search_fields = ('user__username', 'challenge__title')
    date_hierarchy = 'updated_at'

    def get_queryset(self, request):
        # Optimize queries
        return super().get_queryset(request).select_related('user', 'challenge')

# Without it (return super()......above):

# Django makes 3 separate database queries per UserProgress row:

# Get UserProgress
# Get related User (when displaying user.username)
# Get related Challenge (when displaying challenge.title)


# If you have 100 UserProgress records, that's 300 queries 🐌

# With it:

# Django makes 1 query using SQL JOINs
# Gets UserProgress + User + Challenge all at once
# 100 records = 1 query ⚡
