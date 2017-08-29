from django.contrib.auth import authenticate
from rest_framework import serializers
from . import exceptions
from .models import Profile, PhoneNumber, PhoneNumberConfirmation
from django.contrib.auth.models import User
from django.utils import timezone


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('avatar_url', 'bio', 'full_name')


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'profile')
        depth = 1


class UserWithoutProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', )


class SignUpSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(write_only=True)
    username = serializers.CharField()

    def create(self, validated_data):
        phone_number = validated_data.get('phone_number')
        user = User.objects.create_user(username=validated_data.get('username'), password=validated_data.get('password'))
        PhoneNumber.objects.create(user=user, number=phone_number)
        return user


class MyProfileSerializer(serializers.ModelSerializer):
    money = serializers.ReadOnlyField()
    user = UserWithoutProfileSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('money', 'avatar_url' ,'user', 'full_name', 'show_phone_number', 'location', 'bio')


class UpdateProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('avatar_url',)


class FollowSerializers(serializers.ModelSerializer):
    following = serializers.BooleanField(read_only=True)
    username = serializers.CharField(read_only=True)
    profile = ProfileSerializer(read_only=True)
    requester = UserSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'profile', 'following', 'requester')
        depth = 1


class RequestConfirmation(serializers.Serializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(label="Username")
    password = serializers.CharField(label="Password", style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        if username and password:
            user = authenticate(username=username, password=password)

            if user:
                # From Django 1.10 onwards the `authenticate` call simply
                # returns `None` for is_active=False users.
                # (Assuming the default `ModelBackend` authentication backend.)
                if not user.is_active:
                    msg = 'User account is disabled.'
                    raise serializers.ValidationError(msg, code='authorization')
            else:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "username" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField(label="Username")
    password = serializers.CharField(label="Password", style={'input_type': 'password'})
    confirm_code = serializers.IntegerField(label="ConfirmCode")

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        confirm_code = attrs.get('confirm_code')
        if username and password and confirm_code:
            user = authenticate(username=username, password=password)

            if user:
                # From Django 1.10 onwards the `authenticate` call simply
                # returns `None` for is_active=False users.
                # (Assuming the default `ModelBackend` authentication backend.)
                phone_confirmation = PhoneNumberConfirmation.objects.get(user=user)
                if timezone.now() - phone_confirmation.last_request_time > timezone.timedelta(minutes=5):
                    raise serializers.ValidationError('please request again', code=503)
                if confirm_code != phone_confirmation.confirm_code:
                    msg = 'bad confirmation code'
                    raise serializers.ValidationError(msg, code='authorization')
                if not user.is_active:
                    msg = 'User account is disabled.'
                    raise serializers.ValidationError(msg, code='authorization')
            else:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "username" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
