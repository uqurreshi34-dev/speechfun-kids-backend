from django.urls import path
from .views import (
    LetterList, WordListByLetter,
    ChallengeListByLetterAndDifficulty, ChallengeDetail,
    CommentListCreate, CommentDetail,
    UserProgressList, UserProgressCreateOrUpdate,
    get_user_progress, update_progress, YesNoQuestionList, FunctionalPhraseList
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
    # NEW function-based views for Token auth
    path('progress/', get_user_progress, name='get-user-progress'),
    path('progress/update/', update_progress, name='update-progress'),
    # Old class-based views (keep for backwards compatibility if needed)
    #     path('progress/', UserProgressList.as_view(), name='user-progress-list'),
    #     path('progress/update/', UserProgressCreateOrUpdate.as_view(),
    #          name='user-progress-update'),
    path('yes-no-questions/', YesNoQuestionList.as_view(), name='yes-no-questions'),
    path('functional-phrases/', FunctionalPhraseList.as_view(),
         name='functional-phrases'),
]
