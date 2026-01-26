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
# class RegisterView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = RegisterSerializer
#     permission_classes = [permissions.AllowAny]

#     def create(self, request, *args, **kwargs):
#         print("=== Registration Data ===")
#         print(request.data)

#         serializer = self.get_serializer(data=request.data)

#         if not serializer.is_valid():
#             print("❌ Validation errors:", serializer.errors)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         user = serializer.save()   # creates inactive user
#         print(f"✅ User created: {user.username}")

#         # TEMPORARILY SKIP EMAIL - Just activate user immediately
#         user.is_active = True
#         user.save()
#         print("✅ User activated (email verification skipped)")

#         return Response(
#             {
#                 "detail": "Registration successful! You can now login.",
#                 "email": user.email,
#             },
#             status=status.HTTP_201_CREATED
#         )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        print("=== Registration Data ===")
        print(request.data)

        serializer = self.get_serializer(data=request.data)

        # Don't use raise_exception - handle errors manually
        if not serializer.is_valid():
            print("❌ Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()   # creates inactive user
        print(f"✅ User created: {user.username}")

        # Create verification token
        token_obj = EmailVerificationToken.objects.create(user=user)

        # Send email
        email_sent = send_verification_email(user, token_obj.token)

        if not email_sent:
            user.delete()
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
