from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import Profile
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer, ProfileSerializer


# Create your views here.


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(username=response.data['username'])
        Token.objects.create(user=user)  # Create token for new user
        Profile.objects.create(user=user)  # Auto-create profile
        return response


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ← assumes validate() in loginserializer in serializers.py sets self.user
        user = serializer.user

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
    user, created = User.objects.get_or_create(
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
