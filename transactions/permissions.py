from rest_framework import permissions


class IsBuyerOfTransaction(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.buyer


class IsOwnerOfTransactionsPost(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.post.sender
