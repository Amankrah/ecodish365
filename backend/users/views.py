from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import UserFollowing, UserActivityLog
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, UserPublicSerializer,
    UserFollowingSerializer, UserActivityLogSerializer
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            user = User.objects.get(email=response.data['email'])
            token, created = Token.objects.get_or_create(user=user)
            response.data['token'] = token.key
            
            # Log user registration activity
            UserActivityLog.objects.create(
                user=user,
                activity_type='profile_updated',
                details={'action': 'user_registered'}
            )
        
        return response


class UserLoginView(generics.GenericAPIView):
    """User login endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        username_or_email = request.data.get('username_or_email')
        password = request.data.get('password')
        
        if username_or_email and password:
            # Use the custom authentication backend that handles both username and email
            user = authenticate(username=username_or_email, password=password)
            
            if user:
                token, created = Token.objects.get_or_create(user=user)
                
                # Update last active
                from django.utils import timezone
                user.last_active = timezone.now()
                user.save(update_fields=['last_active'])
                
                return Response({
                    'token': token.key,
                    'user': UserProfileSerializer(user).data
                })
            else:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        return Response(
            {'error': 'Username/email and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user profiles"""
    queryset = User.objects.all()
    lookup_field = 'username'
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve'] and self.request.user != self.get_object():
            return UserPublicSerializer
        return UserProfileSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        if self.action == 'list':
            # Only show public profiles in list view
            return User.objects.filter(profile_public=True)
        return User.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        # Allow users to see their own profile, or public profiles
        if user == request.user or user.profile_public:
            return super().retrieve(request, *args, **kwargs)
        else:
            return Response(
                {'error': 'Profile is private'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    def update(self, request, *args, **kwargs):
        # Only allow users to update their own profile
        if self.get_object() != request.user:
            return Response(
                {'error': 'Can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response = super().update(request, *args, **kwargs)
        
        # Log profile update
        if response.status_code == status.HTTP_200_OK:
            UserActivityLog.objects.create(
                user=request.user,
                activity_type='profile_updated',
                details={'fields_updated': list(request.data.keys())}
            )
        
        return response
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, username=None):
        """Follow a user"""
        user_to_follow = self.get_object()
        
        if user_to_follow == request.user:
            return Response(
                {'error': 'Cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        following, created = UserFollowing.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if created:
            # Log activity
            UserActivityLog.objects.create(
                user=request.user,
                activity_type='user_followed',
                details={'followed_user': user_to_follow.username}
            )
            
            return Response({'message': f'You are now following {user_to_follow.username}'})
        else:
            return Response(
                {'message': f'You are already following {user_to_follow.username}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unfollow(self, request, username=None):
        """Unfollow a user"""
        user_to_unfollow = self.get_object()
        
        try:
            following = UserFollowing.objects.get(
                follower=request.user,
                following=user_to_unfollow
            )
            following.delete()
            return Response({'message': f'You have unfollowed {user_to_unfollow.username}'})
        except UserFollowing.DoesNotExist:
            return Response(
                {'error': f'You are not following {user_to_unfollow.username}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def followers(self, request, username=None):
        """Get user's followers"""
        user = self.get_object()
        followers = UserFollowing.objects.filter(following=user)
        serializer = UserFollowingSerializer(followers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def following(self, request, username=None):
        """Get users that this user follows"""
        user = self.get_object()
        following = UserFollowing.objects.filter(follower=user)
        serializer = UserFollowingSerializer(following, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user's profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def activity(self, request):
        """Get current user's activity log"""
        activities = UserActivityLog.objects.filter(user=request.user)[:50]
        serializer = UserActivityLogSerializer(activities, many=True)
        return Response(serializer.data)


class UserSearchView(generics.ListAPIView):
    """Search users by username or name"""
    serializer_class = UserPublicSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if query:
            return User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query),
                profile_public=True
            ).distinct()
        return User.objects.none()
