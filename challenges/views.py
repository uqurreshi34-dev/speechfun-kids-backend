import traceback
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import (Letter, Word, Challenge, Comment,
                     UserProgress, YesNoQuestion, FunctionalPhrase)
from .serializers import (LetterSerializer, WordSerializer,
                          ChallengeSerializer, CommentSerializer,
                          UserProgressSerializer, YesNoQuestionSerializer,
                          FunctionalPhraseSerializer)


class LetterList(generics.ListAPIView):
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [permissions.AllowAny]


class WordListByLetter(generics.ListAPIView):
    serializer_class = WordSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # kwargs comes from URL (e.g. /letters/5/words/)
        letter_id = self.kwargs['letter_id']
        # returns only words belonging to that letter
        return Word.objects.filter(letter_id=letter_id)


class ChallengeListByLetterAndDifficulty(generics.ListAPIView):
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.AllowAny]
# Uses BOTH URL parameter (letter_id) and query parameter (?difficulty=medium)
# Optional filtering by difficulty
# Final ordering: first by difficulty, then alphabetically by title
# Example URLs:
# GET /letters/3/challenges/ → all challenges for letter 3
# GET /letters/3/challenges/?difficulty=hard → only hard ones

    def get_queryset(self):
        letter_id = self.kwargs.get('letter_id')
        # .get() instead of [] → safer (won't raise KeyError)
        difficulty = self.request.query_params.get('difficulty', None)
        queryset = Challenge.objects.filter(word__letter_id=letter_id)
        if difficulty in ['easy', 'medium', 'hard']:
            queryset = queryset.filter(difficulty=difficulty)
        return queryset.order_by('difficulty', 'title')


class ChallengeDetail(generics.RetrieveAPIView):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    # looks for primary key in URL (default anyway)
    lookup_field = 'pk'
    permission_classes = [permissions.AllowAny]

# Two behaviors in one class:
# GET → list all comments for a challenge (newest first)
# POST → create new comment


class CommentListCreate(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        challenge_id = self.kwargs['challenge_id']
        return Comment.objects.filter(challenge_id=challenge_id).order_by('-created_at')

# perform_create() is very important:
# Automatically sets user = logged-in user
# Automatically sets challenge from URL
# Prevents user from sending fake user or challenge in JSON
# SEE BOTTOM FOR DETAILED EXPN!!!!!
    def perform_create(self, serializer):
        challenge = get_object_or_404(
            Challenge, pk=self.kwargs['challenge_id'])
        serializer.save(
            user=self.request.user,  # forced — cannot be faked
            challenge=challenge)  # forced from URL — cannot be faked

# This view supports:

# GET    (anyone)
# PUT    (only owner)
# PATCH  (only owner)
# DELETE (only owner)


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'pk'

    # get_permissions() → dynamic permissions depending on HTTP method - overriding get_permissions
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()
        # otherwise if not Put Patch Delete, tell parent class (RetrieveUpdateDestroyAPIView to
        # call it's own get_permissions method and do what it normally does)

# Classic Django REST permission
# Read (GET, HEAD, OPTIONS) → always allowed
# Write (PUT, PATCH, DELETE) → only if obj.user == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

# UPDATED: Changed to function-based view for Token auth
# Function-based views with @api_view and @permission_classes decorators are explicitly designed
# for Token authentication
# Class-based views use different authentication flow that requires additional configuration
# Both are modern and valid - DRF supports both equally well
# Token auth with decorators is just more straightforward and explicit


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_user_progress(request):
#     """Get all progress for the authenticated user"""
#     progress = UserProgress.objects.filter(user=request.user)
#     serializer = UserProgressSerializer(progress, many=True)
#     return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_progress(request):
    """Get all user progress (both letter and yes/no challenges)"""
    try:
        progress_items = UserProgress.objects.filter(user=request.user)

        result = []
        for item in progress_items:
            # Determine which ID to return
            if item.challenge:
                challenge_id = item.challenge.id
            elif item.yes_no_question:
                challenge_id = item.yes_no_question.id
            elif item.functional_phrase:
                challenge_id = item.functional_phrase.id
            else:
                continue

            result.append({
                'challenge': challenge_id,
                'type': item.challenge_type,
                'completed': item.completed,
                'score': item.score
            })

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"❌ Get progress error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# UPDATED: Changed to function-based view for Token auth


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_progress(request):
    challenge_id = request.data.get('challenge')
    challenge_type = request.data.get(
        'challenge_type', 'letter')  # 'letter' or 'yes_no'
    completed = request.data.get('completed', False)
    score = request.data.get('score', 0)

    print(f"=== PROGRESS UPDATE ===")
    print(f"User: {request.user.username}")
    print(f"Challenge ID: {challenge_id}")
    print(f"Type: {challenge_type}")
    print(f"Completed: {completed}")

    if not challenge_id:
        return Response({'error': 'Challenge ID required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if challenge_type == 'yes_no':
            # Handle Yes/No questions
            try:
                yes_no_q = YesNoQuestion.objects.get(id=challenge_id)
            except YesNoQuestion.DoesNotExist:
                return Response({'error': 'Yes/No question not found'}, status=status.HTTP_404_NOT_FOUND)

            progress, created = UserProgress.objects.get_or_create(
                user=request.user,
                yes_no_question=yes_no_q,
                defaults={
                    'completed': completed,
                    'score': score,
                    'challenge_type': 'yes_no'
                }
            )

            if not created:
                progress.completed = completed
                progress.score = score
                progress.save()

            print(f"✅ Yes/No progress saved: {progress}")

        elif challenge_type == 'functional':
            # Handle functional language phrases
            try:
                func_phrase = FunctionalPhrase.objects.get(id=challenge_id)
            except FunctionalPhrase.DoesNotExist:
                return Response({'error': 'Functional phrase not found'}, status=status.HTTP_404_NOT_FOUND)

            progress, created = UserProgress.objects.update_or_create(
                user=request.user,
                functional_phrase=func_phrase,
                defaults={
                    'completed': completed,
                    'score': score,
                    'challenge_type': 'functional'
                }
            )

            if not created:
                progress.completed = completed
                progress.score = score
                progress.save()

        else:  # 'letter' type (default)
            # Handle regular letter challenges
            try:
                challenge = Challenge.objects.get(id=challenge_id)
            except Challenge.DoesNotExist:
                return Response({'error': 'Challenge not found'}, status=status.HTTP_404_NOT_FOUND)

            progress, created = UserProgress.objects.get_or_create(
                user=request.user,
                challenge=challenge,
                defaults={
                    'completed': completed,
                    'score': score,
                    'challenge_type': 'letter'
                }
            )

            if not created:
                progress.completed = completed
                progress.score = score
                progress.save()

            print(f"✅ Letter progress saved: {progress}")

        return Response({
            'success': True,
            'progress': {
                'challenge': challenge_id,
                'type': challenge_type,
                'completed': completed,
                'score': score
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"❌ Progress update error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def update_progress(request):
#     """Update or create progress for a challenge"""
#     challenge_id = request.data.get('challenge')

#     if not challenge_id:
#         return Response({'error': 'Challenge ID required'}, status=status.HTTP_400_BAD_REQUEST)

#     challenge = get_object_or_404(Challenge, pk=challenge_id)

#     progress, created = UserProgress.objects.update_or_create(
#         user=request.user,
#         challenge=challenge,
#         defaults={
#             'completed': request.data.get('completed', False),
#             'score': request.data.get('score', 0)
#         }
#     )

#     serializer = UserProgressSerializer(progress)
#     status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
#     return Response(serializer.data, status=status_code)


# Keep the old class-based views for backwards compatibility (if needed)


# Only shows progress of currently logged-in user
# Login required


class UserProgressList(generics.ListAPIView):
    serializer_class = UserProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)

# Key pattern: upsert (update or create)

# Uses update_or_create() → very convenient
# Looks for record with exactly this user + challenge
# If exists → updates completed and score
# If not → creates new record
# Returns 201 Created or 200 OK accordingly


class UserProgressCreateOrUpdate(APIView):
    permission_classes = [permissions.IsAuthenticated]
# APIView provides: Dispatcher that looks for methods named exactly get, post, put, etc.
# .dispatch() logic that calls the matching method (if it exists)
# (post, get) - this is just a convention that DRF's dispatcher recognizes

    def post(self, request):
        challenge_id = request.data.get('challenge')
        challenge = get_object_or_404(Challenge, pk=challenge_id)
        # This is multiple assignment (also called tuple unpacking) — one of Python's nicest features.
        # The method you are calling: UserProgress.objects.update_or_create(…)
        # always returns a tuple with exactly two items:
        #   (the_model_instance, boolean_created_or_not)
        progress, created = UserProgress.objects.update_or_create(
            user=request.user, challenge=challenge,
            defaults={'completed': request.data.get(
                'completed', False), 'score': request.data.get('score', 0)}
        )
        serializer = UserProgressSerializer(progress)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)


class YesNoQuestionList(generics.ListAPIView):
    queryset = YesNoQuestion.objects.all()
    serializer_class = YesNoQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]  # Not public read


class FunctionalPhraseList(generics.ListAPIView):
    queryset = FunctionalPhrase.objects.all()
    serializer_class = FunctionalPhraseSerializer
    permission_classes = [permissions.IsAuthenticated]


# The flow when someone sends POST → /comments/

# ListCreateAPIView.post() is called (you didn't write it — it's inherited)
# post() calls self.create(request, *args, **kwargs)
# create() does:
# serializer = self.get_serializer(data=request.data)
# serializer.is_valid(raise_exception=True)
# self.perform_create(serializer)   ←←← this is the hook you override
# create success headers
# return Response(serializer.data, status=201, headers=...)

# Your perform_create() runs → you tell the serializer which extra fields to set
# serializer.save(...) actually creates the object in the database

# Why overriding perform_create() is the cleanest & safest choice here
# Your Comment model probably looks something like this:
# class Comment(models.Model):
#     user      = models.ForeignKey(User, on_delete=CASCADE)
#     challenge = models.ForeignKey(Challenge, on_delete=CASCADE)
#     text      = models.TextField()
#     ...
# Common problems if you don't override perform_create():

# User can send "user": 999 or "challenge": 777 in JSON → and create comment for anyone / any challenge
# Security hole — very serious in real apps

# By doing:
# Pythondef perform_create(self, serializer):
#     challenge = get_object_or_404(Challenge, pk=self.kwargs['challenge_id'])
#     serializer.save(
#         user=self.request.user,     # forced — cannot be faked
#         challenge=challenge         # forced from URL — cannot be faked
#     )
# You achieve four very important things at once:

# Security — user & challenge are never taken from request.data
# Convenience — client doesn't have to (and cannot) send them
# DRF style — you only override the tiny hook, rest of create() / post() stays default
# Clean serializer — you can make user and challengeread_only=True in the serializer

# class CommentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Comment
#         fields = ['id', 'text', 'created_at', 'user', 'challenge']
#         read_only_fields = ['user', 'challenge', 'created_at']
# → client only sends { "text": "Great challenge!" } — perfect.
# When would you override create() instead?
# Only if you need to do something more exotic, for example:

# Return different serializer for response
# Create multiple objects at once
# Run extra logic after save but before response
# Change status code conditionally
# Wrap in transaction with side effects

# Example (rare):
# def create(self, request, *args, **kwargs):
#     serializer = self.get_serializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#     self.perform_create(serializer)
#     # custom logic here...
#     headers = self.get_success_headers(serializer.data)
#     return Response({"message": "Comment created!", "data": serializer.data},
#                     status=status.HTTP_201_CREATED, headers=headers)
# But 95% of the time → just perform_create() is exactly what you want.
# So in short:
# ListCreateAPIView gives you a ready-made, secure, well-tested POST handler.
# You override perform_create() to tell it "add these extra fields automatically" — that's the intended design of Django REST framework.
