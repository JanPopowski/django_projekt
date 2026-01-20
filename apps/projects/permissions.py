from rest_framework import permissions

class IsTeamMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        if hasattr(obj, 'members'):
            return request.user in obj.members.all()
        
        if hasattr(obj, 'team'):
            return request.user in obj.team.members.all()
        return False

class IsTeamOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user