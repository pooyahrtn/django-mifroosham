from django.contrib.auth import authenticate
from rest_framework import serializers
from . import exceptions
from .models import User, PhoneNumber, PhoneNumberConfirmation, Review, Follow

from django.utils import timezone

user_fields = ('score', 'avatar_url', 'bio', 'full_name', 'count_of_rates', 'location', 'show_phone_number', 'username')


#
# class ProfileSerializer(serializers.ModelSerializer):
#     score = serializers.ReadOnlyField()
#     count_of_rates = serializers.ReadOnlyField()
#
#     class Meta:
#         model = User
#         fields = ('score', 'avatar_url', 'bio', 'full_name', 'count_of_rates', 'location', 'show_phone_number')
#

class UserSerializer(serializers.ModelSerializer):
    score = serializers.ReadOnlyField()
    count_of_rates = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = user_fields
        depth = 1


class FollowNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('n_followers', 'n_followings')


class UserWithFollowCountSerializer(UserSerializer):
    follow = FollowNumberSerializer()

    class Meta:
        model = User
        fields = user_fields + ('follow',)


# class UserWithoutProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('username',)



class MyProfileSerializer(UserSerializer):
    money = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = user_fields + ('money',)


class UpdateProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('avatar_url',)


class FollowSerializers(serializers.ModelSerializer):
    following = serializers.BooleanField(read_only=True)
    username = serializers.CharField(read_only=True)
    requester = UserSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'following', 'requester')
        depth = 1


class SignUpSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    phone_number = serializers.CharField(write_only=True)
    username = serializers.CharField()

    def create(self, validated_data):
        phone_number = validated_data.get('phone_number')
        user = User.objects.create_user(username=validated_data.get('username'),
                                        password=validated_data.get('password'), full_name=validated_data.get('username'))
        phone, created = PhoneNumber.objects.get_or_create(number=phone_number)
        if not created:
            raise exceptions.CreateUserException(code=502, detail='this phone number exists')
        return user


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


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ('rate', 'comment', 'reviewer', 'uuid', 'transaction', 'image_url')
