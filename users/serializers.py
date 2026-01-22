from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Profile

# all the fields listed in the UserSerializer are real,
# built-in fields of Django's default User model.
# other built-in fields: password, is_active, is_staff, is_superuser, date_joined, last_login,
# groups, user_permissions


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
# create() IS a built-in method in ModelSerializer - we're overriding it
# default version: return self.Meta.model.objects.create(**validated_data)
# That's why you can (and often should) override it when you need custom creation logic —
# especially when dealing with passwords or nested objects.
# Client → raw JSON → serializer.is_valid() → validated_data (clean & trusted dict) →
# your create(validated_data) → creates real object
# So when you see validated_data inside create() or update() — think:
# “This is the safe, already-checked version of what the user sent me.”
# validate_data is a Python dictionary
# validated_data is already safe to use — you don’t need to do extra .get(), .strip(), type checks, etc.

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


# Here's why you should not use ModelSerializer in this case:
# 1. Login does not create or update a model instance

# A login request receives username + password → it authenticates the user → it returns a token / session.
# Nothing is being saved to the database.
# No User object is created or modified during login.
# ModelSerializer is designed for situations where you do want to .create() or .update() model instances (CRUD operations on models like Post, Comment, Product, etc.).

# If you used ModelSerializer for login, you would get:

# Automatic .create() and .update() methods that you don't want and should never allow on a login endpoint.
# DRF would expect (and try to enforce) model-level behavior that doesn't make sense here.

# 2. The data is not coming from / going to a model directly
# ModelSerializer expects to be tightly coupled to a Django model
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
# validate is a built-in designed hook in DRF.
# To do any other validation that requires access to multiple fields, add a method called .validate()
# to your Serializer subclass. This method takes a single argument, which is a dictionary of field
# values. It should raise a serializers.ValidationError if necessary, or just return the validated values."
# ** is dictionary unpacking in python. user = authenticate(**data) is exactly the same as writing:
# user = authenticate(
#     username=data['username'],
#     password=data['password']
# )

    def validate(self, data):  # see expn at bottom
        user = authenticate(**data)
        if user and user.is_active:
            # Attach user so the view can access it easily (very common)
            self.user = user
            return data           # ← return the dict, not the user
        raise serializers.ValidationError("Incorrect Credentials")


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'bio']


# Quick Summary of validate
# Is validate() built-in?Yes — it's a hook provided by Serializer (default just returns data)
# When is it called?Automatically during serializer.is_valid() (after field-level validation)
# What does it receive?data = dict of already-validated field values (validated_data)
# Why **data?Dictionary unpacking → turns {'username':…, 'password':…} into username=…, password=…
# Should you return user or data? Usually data (the dict) + optionally self.user = user
