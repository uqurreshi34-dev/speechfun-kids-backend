import traceback
import os
from groq import Groq
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import Profile, EmailVerificationToken
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer, ProfileSerializer
from .emails import send_verification_email


# Create your views here.

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        print("=== Registration Data ===")
        print(request.data)

        serializer = self.get_serializer(data=request.data)

        # Let DRF handle validation (raises 400 automatically if invalid)
        try:
            user = serializer.save()  # creates inactive user
            print(f"✅ User created: {user.username} (ID: {user.id})")

            # Clean up any old tokens (prevents unique constraint errors)
            EmailVerificationToken.objects.filter(user=user).delete()
            print("Old tokens cleaned")

            # Create new token
            token_obj = EmailVerificationToken.objects.create(user=user)
            print(f"Token created: {token_obj.token}")

            # Send email
            email_sent = send_verification_email(user, token_obj.token)

            if not email_sent:
                token_obj.delete()
                # Optional: delete user if email is critical
                # user.delete()
                return Response(
                    {"detail": "Failed to send verification email. Please try again later."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            return Response(
                {
                    "detail": "Registration successful! Please check your email to verify your account.",
                    "email": user.email,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            print(f"❌ CRASH during registration: {type(e).__name__}: {e}")
            traceback.print_exc()
            return Response(
                {"detail": f"Server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token_str = request.query_params.get('token')
        if not token_str:
            return Response({"detail": "Token is required"}, status=400)

        try:
            token_obj = EmailVerificationToken.objects.get(token=token_str)
        except EmailVerificationToken.DoesNotExist:
            return Response({"detail": "Invalid token"}, status=400)

        if not token_obj.is_valid():  # is_valid() methid in EmailVerification token
            token_obj.delete()  # clean up expired
            return Response({"detail": "Token has expired"}, status=410)

        user = token_obj.user
        if user.is_active:
            return Response({"detail": "Account already verified"}, status=200)

        user.is_active = True
        user.save()

        # Optional: clean up token after successful verification
        token_obj.delete()

        return Response({
            "detail": "Email verified successfully! You can now log in."
        })


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ← assumes validate() in loginserializer in serializers.py sets self.user
        user = serializer.user

        if not user.is_active:
            return Response(
                {"detail": "Please verify your email before logging in."},
                status=status.HTTP_403_FORBIDDEN
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Profile.objects.get(user=self.request.user)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def get_or_create_token(request):
    email = request.data.get('email')
    username = request.data.get('username')

    if not email:
        return Response({'error': 'Email is required'}, status=400)

    # Get or create user
    user, _ = User.objects.get_or_create(
        email=email,
        defaults={'username': username or email.split('@')[0]}
    )

    # Get or create token
    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user_id': user.id,
        'username': user.username
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def get_word_help(request):
    """AI helper to explain words to kids using Groq"""
    word = request.data.get('word')

    if not word:
        return Response({'error': 'Word is required'}, status=400)

    try:
        # Get API key from environment
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("❌ GROQ_API_KEY not found in environment")
            return Response({'error': 'AI helper not configured'}, status=500)

        # Initialize Groq client
        client = Groq(api_key=api_key)

        print(f"🤖 Getting AI help for word: {word}")

        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a friendly AI helper for kids ages 5-8 learning speech. 
                    Explain the word "{word}" in a fun, simple way. Include:
                    1. What it means (in 1 simple sentence)
                    2. A fun example sentence using the word
                    3. One fun fact about it

                    Keep it under 50 words total. Be enthusiastic and use emojis!"""
                }
            ],
            model="llama-3.3-70b-versatile",  # Groq's best free model
            max_tokens=200,
            temperature=0.7,
        )

        explanation = chat_completion.choices[0].message.content
        print(f"✅ AI response: {explanation[:100]}...")

        return Response({'explanation': explanation})

    except Exception as e:
        print(f"❌ AI error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return Response({
            'error': 'AI helper is taking a break. Try again in a moment! 😊'
        }, status=500)
