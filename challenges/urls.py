from django.urls import path
from .views import (
    LetterList, WordListByLetter,
    ChallengeListByLetterAndDifficulty, ChallengeDetail,
    CommentListCreate, CommentDetail,
    UserProgressList, UserProgressCreateOrUpdate
)

urlpatterns = [
    path('letters/', LetterList.as_view(), name='letter-list'),
    path('letters/<int:letter_id>/words/',
         WordListByLetter.as_view(), name='words-by-letter'),
    path('letters/<int:letter_id>/challenges/',
         ChallengeListByLetterAndDifficulty.as_view(), name='challenges-by-letter'),
    path('challenges/<int:pk>/', ChallengeDetail.as_view(), name='challenge-detail'),
    path('challenges/<int:challenge_id>/comments/',
         CommentListCreate.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetail.as_view(), name='comment-detail'),
    path('progress/', UserProgressList.as_view(), name='user-progress-list'),
    path('progress/update/', UserProgressCreateOrUpdate.as_view(),
         name='user-progress-update'),
]
