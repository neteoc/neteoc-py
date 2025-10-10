# User Profile Enhancements Plan

**Author**: Sarah Mitchell
**Date**: 2025-08-04
**Epic**: Enhanced User Profile Management for Multi-Organization Disaster Response

## Overview

This plan outlines comprehensive enhancements to the NetEOC user profile system to support advanced contact management, profile photos, and secure internal messaging. The improvements focus on multi-organizational context awareness, administrative controls, and reusable UI components that maintain security while improving user experience for disaster response coordination.

## Current State Analysis

The existing user_profile app provides:
- Basic UserProfile extension with roster IDs and drivers license info
- Normalized Address model with coordinate support
- Public profile fields with visibility controls
- API endpoint for check-in auto-population
- Organization-aware access controls

## Proposed Enhancements

### 1. Profile Photos with Gravatar Integration
- User-uploaded profile photos with automatic Gravatar fallback
- Configurable photo size limits and format validation
- Integration with existing public profile visibility controls

### 2. Context-Aware Contact Information
- Organization-specific email addresses and phone numbers
- Global contact info that displays across all organizational contexts
- Priority-based contact selection for incident commanders

### 3. Administrative Controls
- System-level email verification enforcement (optional)
- Organization-level domain restrictions for member email addresses
- Audit logging for contact information changes

### 4. Internal Messaging System
- Secure messaging without exposing contact information
- Read/unread status tracking with read receipts
- Message archiving (no deletion) for accountability
- Thread-based conversations

### 5. Reusable UI Components
- Template components for profile display across applications
- Standardized contact information presentation
- Messaging interface components

## Technical Architecture

### New Models

#### UserContact
```python
class UserContact(models.Model):
    user = ForeignKey(User)
    organization = ForeignKey(IncidentOrganization, null=True, blank=True)  # None = global
    contact_type = CharField(choices=['EMAIL', 'PHONE'])
    value = CharField(max_length=100)
    is_verified = BooleanField(default=False)
    is_primary = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

#### Message
```python
class Message(models.Model):
    sender = ForeignKey(User, related_name='sent_messages')
    subject = CharField(max_length=200)
    content = TextField()
    sent_at = DateTimeField(auto_now_add=True)
    is_archived_by_sender = BooleanField(default=False)
```

#### MessageRecipient
```python
class MessageRecipient(models.Model):
    message = ForeignKey(Message, related_name='recipients')
    recipient = ForeignKey(User, related_name='received_messages')
    is_read = BooleanField(default=False)
    read_at = DateTimeField(null=True, blank=True)
    is_archived = BooleanField(default=False)
```

### Extended UserProfile
```python
# Add to existing UserProfile
profile_photo = ImageField(upload_to='profile_photos/', null=True, blank=True)
use_gravatar = BooleanField(default=True)
gravatar_email = EmailField(blank=True, help_text="Email for Gravatar (defaults to account email)")
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
**Deliverables:**
- New models and migrations
- Basic admin interfaces
- Unit tests for model functionality

**Files to Create/Modify:**
- `user_profile/models.py` - Add new models and extend UserProfile
- `user_profile/admin.py` - Admin interfaces for new models
- `user_profile/migrations/` - Database migrations
- `user_profile/tests.py` - Model tests

### Phase 2: Contact Management (Week 2)
**Deliverables:**
- Contact management forms and views
- Context-aware contact display logic
- Email verification workflow
- Organization domain enforcement

**Files to Create/Modify:**
- `user_profile/forms.py` - Contact management forms
- `user_profile/views.py` - Contact CRUD views
- `user_profile/templates/user_profile/contacts.html` - Contact management UI
- `user_profile/utils.py` - Contact validation utilities

### Phase 3: Messaging System (Week 3)
**Deliverables:**
- Message composition and display
- Read/unread status tracking
- Read receipts functionality
- Message archiving

**Files to Create/Modify:**
- `user_profile/views.py` - Message views
- `user_profile/forms.py` - Message forms
- `user_profile/templates/user_profile/messages/` - Message templates
- `user_profile/serializers.py` - API serializers

### Phase 4: UI Components & Integration (Week 4)
**Deliverables:**
- Reusable profile components
- Photo upload with Gravatar fallback
- Integration with operations app
- Template components

**Files to Create/Modify:**
- `user_profile/templates/components/` - Reusable components
- `user_profile/templatetags/` - Custom template tags
- `operations/templates/operations/` - Updated to use components

## Key Functions and Methods

### Contact Management
- `get_user_contacts_for_context(user, organization=None)` - Retrieves context-appropriate contact information for display
- `create_user_contact(user, contact_type, value, organization=None)` - Creates new contact entry with validation
- `verify_email_contact(contact_id, verification_token)` - Processes email verification workflow

### Photo Management
- `get_profile_photo_url(user, size=150)` - Returns profile photo URL with Gravatar fallback logic
- `validate_profile_photo(photo_file)` - Validates uploaded photo size and format
- `generate_gravatar_url(email, size=150, default='mp')` - Generates Gravatar URL with specified parameters

### Messaging System
- `compose_message(sender, recipients, subject, content)` - Creates new message with recipient tracking
- `mark_message_read(message_id, user)` - Updates read status and timestamp for specific user
- `get_user_messages(user, archived=False)` - Retrieves user's messages with filtering options
- `archive_message_for_user(message_id, user)` - Archives message for specific user without deletion

### Template Components
- `render_profile_card(user, organization_context=None, show_contact=True)` - Renders standardized profile display
- `render_contact_info(user, organization=None, contact_type='all')` - Displays context-aware contact information
- `render_message_preview(message, user)` - Shows message preview with read status

## Testing Strategy

### Model Tests
- `test_user_contact_creation_and_validation` - Verifies contact creation, uniqueness constraints, and validation rules
- `test_organization_context_filtering` - Ensures contacts are properly filtered by organizational context
- `test_message_recipient_status_tracking` - Validates read/unread status and timestamp functionality
- `test_profile_photo_gravatar_fallback` - Tests photo URL generation with various scenarios
- `test_contact_verification_workflow` - Validates email verification process end-to-end

### View Tests
- `test_contact_management_crud_operations` - Tests create, read, update operations for user contacts
- `test_message_composition_and_delivery` - Verifies message creation and recipient notification
- `test_context_aware_profile_display` - Ensures profile information changes based on organizational context
- `test_unauthorized_contact_access_denied` - Validates security controls for contact information access
- `test_domain_enforcement_for_organization` - Tests organizational email domain restrictions

### Integration Tests
- `test_profile_component_rendering_across_apps` - Verifies reusable components work in operations app
- `test_message_system_with_organization_switching` - Tests messaging across different organizational contexts
- `test_gravatar_integration_with_external_service` - Validates Gravatar API integration and fallback behavior
- `test_email_verification_integration` - Tests complete email verification workflow including notifications

### Security Tests
- `test_contact_information_access_controls` - Ensures proper authorization for viewing contact details
- `test_message_privacy_between_organizations` - Validates messages don't leak across unauthorized org boundaries
- `test_profile_photo_upload_security` - Tests file upload validation and security measures
- `test_email_domain_enforcement_bypass_attempts` - Validates domain restriction cannot be circumvented

## Security Considerations

### Data Protection
- All contact information access controlled by organization membership
- Messages encrypted in transit and stored securely
- Profile photos validated for type and size to prevent attacks
- Email verification tokens expire after 24 hours

### Access Controls
- Contact information visibility respects existing public profile settings
- Message system requires shared organization membership or incident participation
- Administrative controls properly scoped to organization boundaries
- API endpoints maintain existing authentication requirements

### Privacy
- Contact information only visible to authorized users within organizational context
- Messages cannot be deleted (only archived) to maintain accountability
- Profile photos can be disabled in favor of Gravatar-only display
- Email verification is optional and configurable at system level

## Migration Strategy

### Database Changes
- New models will be created with proper indexes and constraints
- Existing UserProfile model extended with backward-compatible fields
- Migration includes data integrity checks and rollback procedures

### Template Updates
- Existing templates gradually updated to use new components
- Old profile display methods deprecated but remain functional
- Component-based approach allows incremental adoption across applications

### API Compatibility
- Existing UserRosterAPIView remains unchanged
- New API endpoints follow established patterns and security models
- API versioning maintains backward compatibility for check-in functionality

## Success Metrics

### User Experience
- Reduced time for incident commanders to locate contact information
- Increased adoption of profile photo usage (target: 60% of active users)
- Improved message response times within disaster response scenarios

### System Performance
- Contact information retrieval under 100ms for organization context switching
- Message delivery and read status updates perform under 200ms
- Profile photo loading with Gravatar fallback completes under 500ms

### Administrative Efficiency
- Reduction in support requests related to contact information visibility
- Streamlined user onboarding with organization-specific contact requirements
- Improved audit trail for contact information changes during incidents

## Rollout Plan

### Phase 1 Deployment
- Deploy models and migrations to staging environment
- Validate data integrity and migration performance
- Test admin interfaces with sample data

### Phase 2 Beta Testing
- Enable contact management for pilot organizations
- Gather feedback on user interface and workflow
- Refine domain enforcement and verification processes

### Phase 3 Full Release
- Deploy messaging system with read receipt functionality
- Roll out reusable components to operations app
- Monitor system performance and user adoption

### Phase 4 Optimization
- Implement caching for frequently accessed contact information
- Add bulk operations for administrative contact management
- Enhance reporting and analytics for organizational administrators

This plan provides a comprehensive roadmap for enhancing the user profile system while maintaining security, performance, and usability standards essential for disaster response operations.
