from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (Letter, Word, Challenge, Comment,
                     UserProgress, YesNoQuestion,
                     FunctionalPhrase)


class LetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Letter
        fields = '__all__'


class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ['id', 'word', 'audio']


class ChallengeSerializer(serializers.ModelSerializer):
    # very common Django pattern when you want to show a related field's
    # value instead of (or in addition to) the foreign key ID
    # Every Challenge is linked to one Letter object via the foreign key letter
    # The actual character (like 'A') lives in the related Letter object's field called letter
    # "Add an extra field to the serialized output called letter_name.
    # Its value should come from → the letter related object → its .letter field."
    word = WordSerializer(read_only=True)   # ← nested
    letter_name = serializers.CharField(
        source='word.letter.letter', read_only=True)

    class Meta:
        model = Challenge
        fields = ['id', 'title', 'description', 'word',  # nested word with audio
                  'letter_name', 'difficulty', 'created_at']


class UserSerializer(serializers.ModelSerializer):  # Helper for comments
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'challenge', 'text', 'created_at']
        read_only_fields = ['user', 'created_at']


class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = ['id', 'challenge', 'yes_no_question', 'functional_phrase',
                  'completed', 'score', 'updated_at']
        read_only_fields = ['updated_at']


class YesNoQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = YesNoQuestion
        fields = ['id', 'scene_description',
                  'question', 'correct_answer', 'visual_url']


class FunctionalPhraseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FunctionalPhrase
        fields = ['id', 'phrase', 'visual_url']
