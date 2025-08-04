# Dedicated Messaging System Proposal

**Author**: Jake Harrison
**Date**: 2025-08-04
**Status**: Future Enhancement
**Priority**: High

## Overview

Implement a comprehensive messaging system as a dedicated Django app to support disaster response communication across organizations. This proposal was extracted from the user profile enhancements scope to focus on rapid MVP delivery while maintaining proper architecture for future messaging capabilities.

## GitHub Issue Content

**Title**: Implement Dedicated Messaging System for Inter-Organization Communication

**Labels**: `enhancement`, `messaging`, `high-priority`

**Description:**
Implement a comprehensive messaging system as a dedicated Django app to support disaster response communication across organizations.

**Requirements:**
- Dedicated `messaging` app with proper separation of concerns
- Thread-based conversation support with parent/child message relationships
- Multi-recipient message delivery (group messaging)
- Organization-scoped message access with cross-org incident commander support
- WebSocket integration for real-time message delivery
- Read/unread status tracking with read receipts
- Message archiving (no deletion) for audit trail compliance

**Technical Architecture:**
```python
# messaging/models.py
class Message(models.Model):
    sender = ForeignKey(User, on_delete=models.PROTECT)
    parent_message = ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    thread_id = UUIDField(default=uuid.uuid4, db_index=True)
    organization = ForeignKey(IncidentOrganization, on_delete=models.CASCADE)
    subject = CharField(max_length=200)
    content = TextField()
    sent_at = DateTimeField(auto_now_add=True)
    is_archived_by_sender = BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['thread_id', 'sent_at']),
            models.Index(fields=['sender', 'sent_at']),
            models.Index(fields=['organization', 'sent_at']),
        ]

class MessageRecipient(models.Model):
    message = ForeignKey(Message, on_delete=models.CASCADE, related_name='recipients')
    recipient = ForeignKey(User, on_delete=models.PROTECT)
    is_read = BooleanField(default=False)
    read_at = DateTimeField(null=True, blank=True)
    is_archived = BooleanField(default=False)

    class Meta:
        unique_together = [['message', 'recipient']]
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['message', 'read_at']),
        ]

class MessageThread(models.Model):
    """Thread grouping for conversation management"""
    thread_id = UUIDField(unique=True, db_index=True)
    subject = CharField(max_length=200)
    created_by = ForeignKey(User, on_delete=models.PROTECT)
    organization = ForeignKey(IncidentOrganization, on_delete=models.CASCADE)
    created_at = DateTimeField(auto_now_add=True)
    last_activity = DateTimeField(auto_now=True)
    is_active = BooleanField(default=True)
```

**Security & Access Control:**
```python
# messaging/permissions.py
def can_send_message(sender, recipient):
    """Check if sender can message recipient based on org relationships"""
    # Same organization
    if share_organization(sender, recipient):
        return True

    # Incident commander relationship
    if is_incident_commander_relationship(sender, recipient):
        return True

    # Admin override
    if sender.is_staff:
        return True

    return False

def can_access_thread(user, thread):
    """Check if user can access message thread"""
    # User is thread creator
    if thread.created_by == user:
        return True

    # User is recipient of any message in thread
    if MessageRecipient.objects.filter(
        message__thread_id=thread.thread_id,
        recipient=user
    ).exists():
        return True

    return False
```

**API Endpoints:**
```python
# messaging/api_urls.py
urlpatterns = [
    # Thread management
    path('threads/', ThreadListCreateView.as_view(), name='thread-list'),
    path('threads/<uuid:thread_id>/', ThreadDetailView.as_view(), name='thread-detail'),
    path('threads/<uuid:thread_id>/messages/', ThreadMessageListView.as_view(), name='thread-messages'),

    # Message operations
    path('messages/', MessageListCreateView.as_view(), name='message-list'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
    path('messages/<int:pk>/read/', MessageMarkReadView.as_view(), name='message-read'),
    path('messages/<int:pk>/archive/', MessageArchiveView.as_view(), name='message-archive'),

    # User message operations
    path('users/messages/inbox/', UserInboxView.as_view(), name='user-inbox'),
    path('users/messages/sent/', UserSentMessagesView.as_view(), name='user-sent'),
    path('users/messages/archived/', UserArchivedMessagesView.as_view(), name='user-archived'),
]
```

**WebSocket Integration:**
```python
# messaging/consumers.py
class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_add(
                f"user_{self.scope['user'].id}",
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_discard(
                f"user_{self.scope['user'].id}",
                self.channel_name
            )

    async def message_notification(self, event):
        """Send message notification to user"""
        await self.send(text_data=json.dumps({
            'type': 'message_notification',
            'message': event['message'],
            'sender': event['sender'],
            'thread_id': event['thread_id'],
            'timestamp': event['timestamp']
        }))
```

**Implementation Plan:**

**Phase 1: Core Messaging Models and Admin (Week 1)**
- Create messaging app structure
- Implement Message, MessageRecipient, MessageThread models
- Create migrations with proper indexes
- Build admin interfaces for message management
- Implement basic access control permissions

**Phase 2: Message Composition and Threading UI (Week 2)**
- Build message composition forms and views
- Implement thread-based conversation display
- Create message list views (inbox, sent, archived)
- Add message search and filtering capabilities
- Implement responsive messaging interface

**Phase 3: WebSocket Real-time Delivery (Week 3)**
- Set up Django Channels and Redis infrastructure
- Implement WebSocket consumers for real-time messaging
- Add real-time message delivery and read receipts
- Create JavaScript client for WebSocket communication
- Implement connection management and reconnection logic

**Phase 4: Integration and Advanced Features (Week 4)**
- Integration with notification system (requires Proposal 2)
- Implement message threading and reply functionality
- Add bulk operations (mark all as read, bulk archive)
- Create mobile-responsive messaging interface
- Performance optimization and caching strategy

**Acceptance Criteria:**
- [ ] Users can send messages to multiple recipients within organization context
- [ ] Incident commanders can message across organizational boundaries
- [ ] Conversation threading maintains message context and history
- [ ] Real-time delivery via WebSocket connections with <1 second latency
- [ ] Message archiving preserves audit trail without deletion capability
- [ ] Mobile-responsive messaging interface works on all devices
- [ ] API endpoints support pagination for large message volumes
- [ ] WebSocket connections support 500+ concurrent users
- [ ] Message search finds content across all user's accessible messages
- [ ] Integration with notification system triggers appropriate alerts

**Performance Requirements:**
- Message sending completes in <200ms
- Thread loading with 100+ messages completes in <500ms
- WebSocket message delivery in <1 second
- API endpoints support pagination for 10,000+ messages
- Real-time typing indicators with minimal bandwidth usage

**Security Requirements:**
- All message content encrypted in transit
- Access control prevents cross-organizational message leaks
- Input sanitization prevents XSS attacks in message content
- Rate limiting prevents message spam (10 messages/minute per user)
- Audit logging tracks all message access and modifications

**Testing Strategy:**
- Unit tests for all models, views, and permissions
- Integration tests for WebSocket functionality
- Load testing with 500+ concurrent WebSocket connections
- Security testing for access control and input validation
- End-to-end testing of complete messaging workflows

**Dependencies:**
- Notification system implementation (Proposal 2) for message alerts
- WebSocket infrastructure setup (Django Channels + Redis)
- Background task processing for email notifications

**Estimated Effort:** 4 weeks

**Risk Mitigation:**
- WebSocket fallback to polling for connection issues
- Message queue for reliable delivery during system maintenance
- Graceful degradation when real-time features unavailable
- Comprehensive error handling and user feedback

## Technical Considerations

### Database Performance
- Proper indexing strategy for high-volume message queries
- Pagination for thread views to handle long conversations
- Archive strategy for old messages to maintain performance

### Scalability
- WebSocket connection pooling and load balancing
- Message queue processing for background operations
- CDN integration for static messaging assets

### Integration Points
- Seamless integration with existing user_profile Contact system
- Organization context switching compatibility
- Incident management workflow integration
- Future mobile app API compatibility

This messaging system will provide NetEOC with enterprise-grade communication capabilities essential for effective disaster response coordination across multiple organizations.
