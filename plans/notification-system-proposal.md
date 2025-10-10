# Complete Notification Infrastructure Proposal

**Author**: Jake Harrison
**Date**: 2025-08-04
**Status**: Future Enhancement
**Priority**: High

## Overview

Build comprehensive notification infrastructure to support real-time communication during disaster response operations. This proposal was extracted from the user profile enhancements scope to focus on rapid MVP delivery while maintaining proper architecture for future notification capabilities.

## GitHub Issue Content

**Title**: Implement Complete Notification System with Real-time Delivery

**Labels**: `enhancement`, `notifications`, `real-time`, `high-priority`

**Description:**
Build comprehensive notification infrastructure to support real-time communication during disaster response operations.

**Requirements:**
- In-app notification center with unread/read status tracking
- Email notification templates for various notification types
- WebSocket delivery for real-time in-app notifications
- Notification preferences management per user
- Push notification support preparation for future mobile apps
- Admin notification broadcasting capabilities
- Notification archiving and cleanup policies

**Technical Architecture:**
```python
# notifications/models.py
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('MESSAGE_RECEIVED', 'New Message'),
        ('CONTACT_VERIFICATION', 'Contact Verification Required'),
        ('INCIDENT_UPDATE', 'Incident Status Update'),
        ('PROFILE_UPDATED', 'Profile Information Updated'),
        ('SYSTEM_ANNOUNCEMENT', 'System Announcement'),
        ('ASSET_CHECKOUT', 'Asset Checked Out'),
        ('ASSET_CHECKIN', 'Asset Checked In'),
        ('SUPPORT_REQUEST', 'Support Request Received'),
        ('USER_CHECKIN', 'User Checked Into Incident'),
        ('USER_CHECKOUT', 'User Checked Out of Incident'),
    ]

    user = ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = CharField(max_length=200)
    message = TextField()
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    read_at = DateTimeField(null=True, blank=True)
    expires_at = DateTimeField(null=True, blank=True, help_text="Auto-cleanup date")

    # Generic relation for linking to any model
    content_type = ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Delivery tracking
    email_sent = BooleanField(default=False)
    email_sent_at = DateTimeField(null=True, blank=True)
    push_sent = BooleanField(default=False)
    push_sent_at = DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['email_sent', 'created_at']),
        ]
        ordering = ['-created_at']

class NotificationPreference(models.Model):
    user = ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    notification_type = CharField(max_length=30, choices=Notification.NOTIFICATION_TYPES)
    email_enabled = BooleanField(default=True)
    in_app_enabled = BooleanField(default=True)
    push_enabled = BooleanField(default=False)

    # Time-based preferences
    quiet_hours_start = TimeField(null=True, blank=True, help_text="Start of quiet hours (no notifications)")
    quiet_hours_end = TimeField(null=True, blank=True, help_text="End of quiet hours")
    timezone = CharField(max_length=50, default='UTC')

    class Meta:
        unique_together = [['user', 'notification_type']]

class NotificationTemplate(models.Model):
    """Email and push notification templates"""
    notification_type = CharField(max_length=30, choices=Notification.NOTIFICATION_TYPES, unique=True)
    email_subject = CharField(max_length=200)
    email_template = TextField(help_text="HTML email template with Django template syntax")
    email_text_template = TextField(help_text="Plain text email template")
    push_title = CharField(max_length=100, blank=True)
    push_body = CharField(max_length=200, blank=True)
    in_app_template = TextField(help_text="In-app notification template")

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

class SystemBroadcast(models.Model):
    """Admin system-wide announcements"""
    title = CharField(max_length=200)
    message = TextField()
    notification_type = CharField(max_length=30, default='SYSTEM_ANNOUNCEMENT')
    created_by = ForeignKey(User, on_delete=models.PROTECT)
    created_at = DateTimeField(auto_now_add=True)

    # Targeting options
    target_all_users = BooleanField(default=True)
    target_organizations = ManyToManyField('operations.IncidentOrganization', blank=True)
    target_active_incidents_only = BooleanField(default=False)

    # Delivery options
    send_email = BooleanField(default=False)
    send_push = BooleanField(default=False)
    expires_at = DateTimeField(help_text="When notification expires")

    # Status tracking
    is_sent = BooleanField(default=False)
    sent_at = DateTimeField(null=True, blank=True)
    recipient_count = PositiveIntegerField(default=0)
```

**Notification Service Layer:**
```python
# notifications/services.py
class NotificationService:
    @staticmethod
    def create_notification(user, notification_type, title, message, related_object=None, **kwargs):
        """Create notification with automatic delivery based on user preferences"""
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            content_object=related_object,
            **kwargs
        )

        # Trigger delivery based on user preferences
        NotificationService.deliver_notification(notification)
        return notification

    @staticmethod
    def deliver_notification(notification):
        """Deliver notification via configured channels"""
        preferences = NotificationService.get_user_preferences(
            notification.user,
            notification.notification_type
        )

        # Real-time in-app delivery
        if preferences.in_app_enabled:
            NotificationService.send_realtime_notification(notification)

        # Email delivery
        if preferences.email_enabled and not NotificationService.in_quiet_hours(preferences):
            NotificationService.send_email_notification.delay(notification.id)

        # Push notification (future)
        if preferences.push_enabled:
            NotificationService.send_push_notification.delay(notification.id)

    @staticmethod
    def send_realtime_notification(notification):
        """Send real-time notification via WebSocket"""
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"user_{notification.user.id}",
            {
                'type': 'notification_message',
                'notification': {
                    'id': notification.id,
                    'type': notification.notification_type,
                    'title': notification.title,
                    'message': notification.message,
                    'created_at': notification.created_at.isoformat(),
                    'url': notification.get_absolute_url() if hasattr(notification, 'get_absolute_url') else None,
                }
            }
        )

    @staticmethod
    def mark_notifications_read(user, notification_ids=None):
        """Mark notifications as read with bulk update"""
        queryset = user.notifications.filter(is_read=False)
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)

        updated_count = queryset.update(is_read=True, read_at=timezone.now())

        # Send real-time update for unread count
        NotificationService.send_unread_count_update(user)
        return updated_count

    @staticmethod
    def get_unread_count(user):
        """Get unread notification count with caching"""
        cache_key = f"unread_notifications:{user.id}"
        count = cache.get(cache_key)

        if count is None:
            count = user.notifications.filter(is_read=False).count()
            cache.set(cache_key, count, 300)  # Cache for 5 minutes

        return count
```

**WebSocket Consumer:**
```python
# notifications/consumers.py
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            # Join user-specific notification group
            await self.channel_layer.group_add(
                f"user_{self.scope['user'].id}",
                self.channel_name
            )

            # Send current unread count on connection
            unread_count = await self.get_unread_count()
            await self.send(text_data=json.dumps({
                'type': 'unread_count',
                'count': unread_count
            }))

            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_discard(
                f"user_{self.scope['user'].id}",
                self.channel_name
            )

    async def notification_message(self, event):
        """Handle new notification"""
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['notification']
        }))

    async def unread_count_update(self, event):
        """Handle unread count update"""
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': event['count']
        }))

    @database_sync_to_async
    def get_unread_count(self):
        return self.scope["user"].notifications.filter(is_read=False).count()
```

**Email Templates:**
```html
<!-- notifications/templates/email/base.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }} - NetEOC</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { background: #dc3545; color: white; padding: 15px; margin: -20px -20px 20px -20px; border-radius: 8px 8px 0 0; }
        .footer { margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NetEOC Notification</h1>
        </div>

        <h2>{{ title }}</h2>
        <p>{{ message }}</p>

        {% if action_url %}
        <p><a href="{{ action_url }}" style="background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">View Details</a></p>
        {% endif %}

        <div class="footer">
            <p>This notification was sent from NetEOC. If you no longer wish to receive these notifications, you can update your preferences in your profile settings.</p>
        </div>
    </div>
</body>
</html>
```

**API Endpoints:**
```python
# notifications/api_urls.py
urlpatterns = [
    # Notification management
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('notifications/unread-count/', UnreadCountView.as_view(), name='unread-count'),

    # Preferences
    path('preferences/', NotificationPreferenceListView.as_view(), name='preference-list'),
    path('preferences/<str:notification_type>/', NotificationPreferenceDetailView.as_view(), name='preference-detail'),

    # Admin broadcasting
    path('admin/broadcast/', SystemBroadcastCreateView.as_view(), name='system-broadcast'),
    path('admin/broadcasts/', SystemBroadcastListView.as_view(), name='broadcast-list'),
]
```

**Frontend JavaScript Integration:**
```javascript
// static/js/notifications.js
class NotificationManager {
    constructor() {
        this.websocket = null;
        this.unreadCount = 0;
        this.connect();
        this.setupEventHandlers();
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;

        this.websocket = new WebSocket(wsUrl);

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.websocket.onclose = () => {
            // Reconnect after 5 seconds
            setTimeout(() => this.connect(), 5000);
        };
    }

    handleMessage(data) {
        switch(data.type) {
            case 'new_notification':
                this.showNotification(data.notification);
                this.updateUnreadCount(this.unreadCount + 1);
                break;
            case 'unread_count':
                this.updateUnreadCount(data.count);
                break;
        }
    }

    showNotification(notification) {
        // Show browser notification if permission granted
        if (Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/static/img/logo.png'
            });
        }

        // Show in-app notification
        this.showInAppNotification(notification);
    }

    updateUnreadCount(count) {
        this.unreadCount = count;
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'block' : 'none';
        }
    }
}

// Initialize notification manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new NotificationManager();
});
```

**Implementation Plan:**

**Phase 1: Core Notification Models and Email Delivery (Week 1)**
- Create notifications app structure
- Implement Notification, NotificationPreference, NotificationTemplate models
- Create migrations with proper indexes
- Build email notification system with templates
- Implement basic admin interfaces

**Phase 2: In-app Notification Center UI (Week 2)**
- Build notification center dropdown component
- Implement notification list views and pagination
- Add mark-as-read and bulk operations
- Create notification preferences management interface
- Build responsive notification UI components

**Phase 3: WebSocket Real-time Delivery (Week 3)**
- Set up Django Channels integration
- Implement WebSocket consumers for real-time notifications
- Add JavaScript client for WebSocket communication
- Implement unread count updates and live notifications
- Add browser notification API integration

**Phase 4: Admin Broadcasting and Advanced Features (Week 4)**
- Implement system broadcast functionality
- Add notification cleanup and archiving policies
- Create advanced admin interfaces for notification management
- Implement quiet hours and timezone support
- Performance optimization and caching strategy

**Acceptance Criteria:**
- [ ] Users receive real-time notifications for messages and system events
- [ ] Email notifications sent reliably with proper HTML templating
- [ ] Notification preferences allow granular control per notification type
- [ ] Admin can broadcast system-wide announcements to targeted user groups
- [ ] Notification center shows unread count with real-time updates
- [ ] Bulk mark-as-read operations work efficiently with 1000+ notifications
- [ ] WebSocket connections handle 500+ concurrent users
- [ ] Browser notifications work with user permission
- [ ] Quiet hours prevent notifications during specified times
- [ ] Notification cleanup policies prevent database bloat

**Performance Requirements:**
- Real-time notification delivery in <1 second via WebSocket
- Email notification processing in <30 seconds
- Unread count queries complete in <50ms with caching
- Notification center loading with 100+ notifications in <300ms
- System broadcasts to 1000+ users complete in <2 minutes

**Security Requirements:**
- Notification content filtered to prevent XSS attacks
- User preferences prevent unauthorized notification access
- Email templates sanitized to prevent injection attacks
- WebSocket connections authenticated and authorized
- Admin broadcast permissions properly scoped

**Testing Strategy:**
- Unit tests for all notification models and services
- Integration tests for email delivery and WebSocket functionality
- Load testing with 1000+ concurrent WebSocket connections
- Security testing for XSS and injection prevention
- End-to-end testing of complete notification workflows

**Dependencies:**
- Email backend configuration (SMTP/SendGrid/etc.)
- WebSocket infrastructure (Django Channels + Redis)
- Background task processing (Celery) for email delivery

**Estimated Effort:** 4 weeks

**Risk Mitigation:**
- Email delivery fallback when SMTP unavailable
- WebSocket fallback to polling for connection issues
- Notification queue processing during system maintenance
- Graceful degradation when real-time features unavailable

## Technical Considerations

### Database Performance
- Efficient indexing for notification queries by user and type
- Automatic cleanup policies for old notifications
- Pagination strategies for large notification volumes

### Scalability
- WebSocket connection management and load balancing
- Email delivery queue processing with retry logic
- CDN integration for notification assets and templates

### Integration Points
- Signal-based notification creation from other apps
- Template customization for different notification types
- Mobile app push notification preparation
- Analytics integration for notification effectiveness tracking

This notification system will provide NetEOC with comprehensive real-time communication capabilities essential for effective disaster response coordination.
