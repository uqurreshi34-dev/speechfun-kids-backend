# challenges/admin.py
from django.contrib import admin
from django import forms
import cloudinary.uploader
from .models import Letter, Word, Challenge, Comment, UserProgress, YesNoQuestion


# Custom form for YesNoQuestion - uploads image/video to Cloudinary
class YesNoQuestionAdminForm(forms.ModelForm):
    visual_file = forms.FileField(
        required=False,
        help_text="Upload image (jpg/png) or short video (mp4). Max 5MB. Will be stored in Cloudinary."
    )

    class Meta:
        model = YesNoQuestion
        fields = ['scene_description', 'question',
                  'answer', 'visual_url']
        widgets = {
            'visual_url': forms.TextInput(attrs={'readonly': 'readonly', 'placeholder': 'Auto-filled after upload'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle new file upload
        if 'visual_file' in self.files and self.files['visual_file']:
            file = self.files['visual_file']

            try:
                safe_question = (
                    instance.question.lower()
                    .replace('?', '')
                    .replace(
                        ' ', '_')
                    .replace('/', '_')
                    .replace('\\', '_')
                )[:50]
                upload_result = cloudinary.uploader.upload(
                    file,
                    resource_type="auto",  # auto-detect image or video
                    folder="speechfun-kids/yesno-visuals",
                    public_id=safe_question,
                    overwrite=True,
                    quality="auto",
                    fetch_format="auto",
                )

                instance.visual_url = upload_result['secure_url']
                print(f"✅ Uploaded to Cloudinary: {instance.visual_url}")

            except Exception as e:
                print(f"❌ Cloudinary upload failed: {e}")
                self.add_error(
                    'visual_file', f"Cloudinary upload failed: {str(e)}")

        if commit:
            instance.save()
        return instance


@admin.register(YesNoQuestion)
class YesNoQuestionAdmin(admin.ModelAdmin):
    form = YesNoQuestionAdminForm
    list_display = ('question', 'answer', 'has_visual')
    list_filter = ('answer',)
    search_fields = ('question', 'scene_description')

    @admin.display(boolean=True, description='Visual')
    def has_visual(self, obj):
        return bool(obj.visual_url)


@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    list_display = ('letter',)          # shows in list view
    search_fields = ('letter',)


# Custom form for Word to handle file upload
class WordAdminForm(forms.ModelForm):
    audio_file = forms.FileField(
        required=False,
        help_text="Upload MP3 file - will be stored in Cloudinary"
    )

    class Meta:
        model = Word
        fields = ['word', 'letter', 'difficulty', 'audio']
        widgets = {  # 'readonly': 'readonly', (put before placeholder once everything is set)
            'audio': forms.TextInput(attrs={'readonly': 'readonly', 'placeholder': 'Auto-filled after upload'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        # If a file was uploaded, send it to Cloudinary
        if 'audio_file' in self.files:
            audio_file = self.files['audio_file']

            try:
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    audio_file,
                    resource_type="auto",
                    folder="speechfun-kids/audios",
                    public_id=f"{instance.word.lower().replace(' ', '_')}"
                )

                # Save the Cloudinary URL
                instance.audio = upload_result['secure_url']
                print(f"✅ Uploaded to Cloudinary: {instance.audio}")
# self.add_error comes from Django's base Form class — and since ModelForm inherits from Form,
# your WordAdminForm automatically gets this method.
            except Exception as e:
                print(f"❌ Cloudinary upload failed: {e}")
                self.add_error(
                    'audio_file', f"Cloudinary upload failed: {str(e)}")

        if commit:
            instance.save()
        return instance


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    form = WordAdminForm
    list_display = ('word', 'letter', 'difficulty', 'has_audio')
    list_filter = ('difficulty', 'letter')
    search_fields = ('word',)

    @admin.display(boolean=True, description='Audio')
    def has_audio(self, obj):
        return bool(obj.audio)


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
            return "✅ Has audio"
        return "❌ No audio"


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
