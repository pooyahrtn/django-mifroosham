from posts.models import Post
from .models import User
# from .serializers import UserWithPostsSerializer
from rest_framework import generics


# class UserPosts(generics.ListAPIView):
#     serializer_class = UserWithPostsSerializer
#     queryset = Post.objects.all()
#     lookup_field = 'sender'
#
#     # def get_queryset(self):
#     #     return User.objects.get(username=self.lookup_field).posts.all()
#     #
#


