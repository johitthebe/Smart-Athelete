from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Message(models.Model):
    """
    Model for messages between coaches and athletes
    """
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="User who sent the message"
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        help_text="User who receives the message"
    )
    subject = models.CharField(
        max_length=200,
        help_text="Message subject"
    )
    body = models.TextField(
        help_text="Message content"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the message has been read"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the message was read"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the message was sent"
    )
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="Parent message if this is a reply"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'recipient']),
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.subject}"

    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
