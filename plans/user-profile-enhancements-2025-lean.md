# Lean User Profile Enhancements Plan

**Author**: Rebecca Chen
**Date**: 2025-08-04
**Epic**: Minimal Viable User Profile Improvements for Pre-Launch NetEOC

## Overview

This lean plan addresses the core user profile requirements for NetEOC's initial launch. Since the system has no users yet, we can implement foundational features efficiently without backward compatibility concerns. Focus is on essential functionality that provides immediate value with minimal complexity.

## Core Requirements (Must Have)

### 1. Basic Profile Photos
- Gravatar integration with email fallback (no uploads initially)
- Simple avatar display in existing templates
- Bootstrap Icons fallback when no Gravatar available

### 2. Essential Contact Management
- Single global email/phone per user (no organization-specific contacts initially)
- Basic email verification (optional)
- Simple contact display in profile and operations views

### 3. Basic Internal Messaging
- Simple message sending between users within same organization
- Read/unread status tracking
- Archive functionality (no deletion)

## Simplified Technical Architecture

### Database Changes (Minimal)

#### Extend UserProfile Model Only
```python
# Add to existing UserProfile model
profile_photo_url = URLField(blank=True, help_text="External photo URL or Gravatar")
use_gravatar = BooleanField(default=True)
primary_email = EmailField(blank=True, help_text="Primary contact email")
primary_phone = CharField(max_length=20, blank=True, help_text="Primary contact phone")
email_verified = BooleanField(default=False)
```

#### Simple Message Models
```python
class SimpleMessage(models.Model):
    sender = ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    subject = CharField(max_length=200)
    content = TextField()
    sent_at = DateTimeField(auto_now_add=True)
    is_read = BooleanField(default=False)
    read_at = DateTimeField(null=True, blank=True)
    is_archived_by_sender = BooleanField(default=False)
    is_archived_by_recipient = BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['sender', 'sent_at']),
        ]
```

## Implementation Plan (2 Weeks)

### Week 1: Core Profile Features
**Days 1-2: Database & Models**
- Extend UserProfile model with new fields
- Create SimpleMessage model
- Run migrations
- Update admin interfaces

**Days 3-5: Basic Views & Forms**
- Update profile form to include contact fields
- Add basic message composition form
- Create simple message list view
- Update existing profile display templates

### Week 2: Integration & Polish
**Days 1-3: Integration**
- Add profile photo display to operations templates
- Integrate contact info into user displays
- Add message link to user profiles

**Days 4-5: Testing & Deployment**
- Basic test coverage for new functionality
- Manual testing of key workflows
- Deploy to staging for validation

## Key Functions (Simplified)

### Photo Management
- `get_profile_photo_url(user, size=150)` - Returns Gravatar URL or Bootstrap icon fallback
- `generate_gravatar_url(email, size=150)` - Simple Gravatar URL generation

### Contact Management
- `get_user_contact_info(user)` - Returns primary email/phone for display
- `send_verification_email(user)` - Basic email verification workflow

### Messaging
- `send_message(sender, recipient, subject, content)` - Create and send message
- `mark_message_read(message, user)` - Mark message as read
- `get_user_messages(user, archived=False)` - Get user's inbox

## Files to Create/Modify

### New Files
- `user_profile/utils.py` - Utility functions for photos and contacts
- `user_profile/templates/user_profile/messages.html` - Simple message interface
- `user_profile/templates/components/profile_photo.html` - Reusable photo component

### Modified Files
- `user_profile/models.py` - Extend UserProfile, add SimpleMessage
- `user_profile/forms.py` - Add contact fields to existing forms
- `user_profile/views.py` - Add message views
- `user_profile/templates/user_profile/profile.html` - Add contact fields
- `operations/templates/operations/` - Use profile photo component

## Essential Tests

### Model Tests
- `test_profile_photo_url_generation` - Gravatar URL generation with fallbacks
- `test_message_creation_and_read_status` - Basic message functionality
- `test_contact_info_validation` - Email/phone format validation

### View Tests
- `test_profile_update_with_contacts` - Profile form handles new fields
- `test_message_send_and_receive` - Basic messaging workflow
- `test_unauthorized_message_access` - Security for message access

### Integration Tests
- `test_profile_photo_display_in_operations` - Photo integration across apps
- `test_contact_info_visibility` - Contact display respects privacy settings

## Security (Minimal but Essential)

### Access Controls
- Messages only between users in same organization
- Contact info respects existing public profile settings
- Basic input sanitization for message content

### Data Protection
- Email verification tokens expire in 24 hours
- Messages cannot be deleted (only archived)
- No sensitive data in logs

## Success Criteria

### User Experience
- Users can set profile photo (Gravatar) in under 30 seconds
- Contact information appears consistently across all user displays
- Messages can be sent and received within organization context

### Technical
- Profile photo loading completes under 2 seconds
- Message sending completes under 500ms
- No performance degradation on existing functionality

## Future Considerations (Not Implemented)

These features are documented for future phases but explicitly NOT included in this lean implementation:

- Organization-specific contact information
- Message threading/conversations
- Real-time notifications
- Profile photo uploads
- Bulk administrative operations
- Advanced email domain restrictions
- WebSocket messaging
- Message search functionality

## Deployment Strategy

### Phase 1: Models & Basic Views
- Deploy new models and migrations
- Test admin functionality
- Validate basic profile updates

### Phase 2: Integration & Launch
- Deploy messaging functionality
- Update operations templates
- Monitor for any performance issues
- Document usage for users

## Rationale for Lean Approach

Since NetEOC has no existing users:
- **No backward compatibility needed** - Can make breaking changes without impact
- **Start simple** - Add complexity based on actual user needs
- **Fast time to market** - Get core functionality live quickly
- **Learn from usage** - Build advanced features based on real user feedback
- **Reduced testing burden** - Fewer edge cases with simpler implementation

This lean approach delivers 80% of the user value with 20% of the implementation complexity, perfect for a pre-launch system where rapid iteration and user feedback are more valuable than comprehensive feature sets.
