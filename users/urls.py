from django.urls import path
from .views import (RegisterView, LoginView, ProfileView,
                    get_or_create_token, VerifyEmailView, get_word_help)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('get-or-create-token/', get_or_create_token, name='get-or-create-token'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('ai-help/', get_word_help, name='ai-help'),

]
