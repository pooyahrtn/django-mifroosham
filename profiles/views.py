import random

from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from django.template import loader
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from posts.models import Feed, ProfilePost
from .serializers import *
from rest_framework import generics, parsers, renderers, status
from django.db import transaction
from .tasks import send_sms
from .exceptions import *
from .permissions import *
import datetime
from notifications.models import FollowNotification


def change_follower_feed(follower, who_followed, is_followed):
    if is_followed:
        posts = who_followed.posts.filter(confirmed_to_show=True)[:10]
        Feed.objects.bulk_create(
            Feed(user=follower, post=post, sort_value=random.randint(0, 2147483647), buyable=True)
            for post in
            posts)
    else:
        Feed.objects.filter(Q(user=follower), Q(post__in=who_followed.posts.all()) | Q(reposter=who_followed)).delete()


class FollowUser(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = FollowSerializers
    lookup_field = 'username'
    permission_classes = (permissions.IsAuthenticated, IsNotOwner)

    @transaction.atomic
    def perform_update(self, serializer):
        user = self.get_object()
        if user.pk == self.request.user.pk:
            raise FollowException(detail='you cant follow your self')
        following = user.follow.followers.filter(username=self.request.user.username).exists()
        if following:
            user.follow.followers.remove(self.request.user)
            user.follow.n_followers -= 1
            self.request.user.follow.n_followings -= 1
        else:
            user.follow.followers.add(self.request.user)
            user.follow.n_followers += 1
            self.request.user.follow.n_followings += 1
            FollowNotification.objects.create_notification(self.request.user, user)
        change_follower_feed(follower=self.request.user, who_followed=user, is_followed=not following)
        self.request.user.follow.save()
        user.follow.save()
        serializer.save(following=not following, requester=self.request.user)


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserWithFollowCountSerializer
    lookup_field = 'username'
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        if not self.request.user.is_anonymous:
            if instance.pk == self.request.user.pk:
                data['money'] = instance.money
            else:
                data['you_follow'] = self.request.user.followings.filter(user=self.get_object()).exists()
        return Response(data)


class MyProfile(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = MyProfileSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOfProfile)

    def get_object(self):
        return self.request.user


class UpdateProfilePhoto(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UpdateProfilePhotoSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOfProfile)

    def get_object(self):
        return self.request.user


class SignUp(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        if User.objects.filter(username=serializer.validated_data.get('username')).exists():
            raise exceptions.CreateUserException()
        user = serializer.save()
        code = random.randint(100000, 999999)
        PhoneNumberConfirmation.objects.create(user=user, confirm_code=code)
        send_sms.delay(user.phone_number.number, code)


class RequestConfirmation(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = RequestConfirmation

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        code = random.randint(100000, 999999)

        phone_confirmation, created = PhoneNumberConfirmation.objects.get_or_create(user=user)
        if not created:
            now = datetime.datetime.now(datetime.timezone.utc)
            delta_time = now - phone_confirmation.last_request_time
            if delta_time < datetime.timedelta(minutes=1):
                return Response({'sent': False, 'reason': 'you just requested'})
            phone_confirmation.confirm_code = code
            phone_confirmation.last_request_time = now
            phone_confirmation.save()
        else:
            phone_confirmation.confirm_code = code
            phone_confirmation.save()

        send_sms.delay(user.phone_number.number, code)

        return Response({'sent': True})


class Login(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class UserReviews(generics.ListAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    lookup_field = 'username'

    def filter_queryset(self, queryset):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return Review.objects.filter(for_user=user)


class UserFollowers(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'

    def get_queryset(self):
        return get_object_or_404(User, username=self.kwargs['username']).follow.followers.all()


class UserFollowings(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'

    def get_queryset(self):
        # it does not look like good. not at all.
        user_follows = get_object_or_404(User, username=self.kwargs['username']).followings.values_list('user',
                                                                                                        flat=True)
        return User.objects.filter(id__in=user_follows).all()
