from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .message_models import Message
from .message_serializers import MessageSerializer, MessageListSerializer


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages between coaches and athletes
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MessageListSerializer
        return MessageSerializer
    
    def get_queryset(self):
        """Return messages where user is sender or recipient"""
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).select_related('sender', 'recipient', 'parent_message')
    
    def create(self, request, *args, **kwargs):
        """Send a new message"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate recipient
        recipient_id = request.data.get('recipient')
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            recipient = User.objects.get(id=recipient_id)
            
            # Check if users can message each other
            # Coaches can message their athletes, athletes can message their coaches
            if request.user.role == 'coach':
                # Check if athlete is assigned to this coach
                from accounts.models import CoachAthleteAssignment
                if not CoachAthleteAssignment.objects.filter(
                    coach=request.user,
                    athlete=recipient,
                    is_active=True
                ).exists():
                    return Response(
                        {"error": "You can only message athletes assigned to you"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif request.user.role == 'athlete':
                # Check if coach is assigned to this athlete
                from accounts.models import CoachAthleteAssignment
                if not CoachAthleteAssignment.objects.filter(
                    coach=recipient,
                    athlete=request.user,
                    is_active=True
                ).exists():
                    return Response(
                        {"error": "You can only message coaches assigned to you"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                return Response(
                    {"error": "Only coaches and athletes can send messages"},
                    status=status.HTTP_403_FORBIDDEN
                )
        except User.DoesNotExist:
            return Response(
                {"error": "Recipient not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Get messages received by the user"""
        messages = self.get_queryset().filter(recipient=request.user)
        
        # Filter by read status
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            messages = messages.filter(is_read=is_read.lower() == 'true')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get messages sent by the user"""
        messages = self.get_queryset().filter(sender=request.user)
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read"""
        message = self.get_object()
        
        # Only recipient can mark as read
        if message.recipient != request.user:
            return Response(
                {"error": "You can only mark your own messages as read"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.mark_as_read()
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """Reply to a message"""
        parent_message = self.get_object()
        
        # Create reply
        data = request.data.copy()
        data['parent_message'] = parent_message.id
        data['recipient'] = parent_message.sender.id
        data['subject'] = f"Re: {parent_message.subject}"
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread messages"""
        count = self.get_queryset().filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['get'])
    def conversation(self, request):
        """Get conversation with a specific user"""
        other_user_id = request.query_params.get('user_id')
        if not other_user_id:
            return Response(
                {"error": "user_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        messages = self.get_queryset().filter(
            Q(sender=request.user, recipient_id=other_user_id) |
            Q(sender_id=other_user_id, recipient=request.user)
        ).order_by('created_at')
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
