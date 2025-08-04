# User Profile Enhancements - Final Implementation Plan

**Author**: Jake Harrison
**Date**: 2025-08-04
**Timeline**: 1 Week MVP Implementation
**Approach**: Streamlined Lean Plan with Normalized Architecture

## Overview

This plan implements essential user profile enhancements as a minimal viable product (MVP) for NetEOC's pre-launch phase. Focus is on normalized contact management and basic profile photos using existing architectural patterns. Advanced features (messaging, notifications, photo uploads) are deferred to future phases with detailed proposals included.

## MVP Scope (1 Week)

### Core Features
1. **Normalized Contact Management** - Email and phone contacts with organization support
2. **Gravatar Profile Photos** - Automatic photo display with Bootstrap Icons fallback
3. **REST API Endpoints** - Contact CRUD with proper authentication/authorization
4. **Template Integration** - Contact display in existing profile and operations views

### Explicitly Excluded (Future Phases)
- Internal messaging system
- Notification infrastructure
- Profile photo uploads/processing
- Email verification workflow
- Caching/performance optimization
- Advanced security testing

## Technical Architecture

### New Contact Model
```python
class Contact(models.Model):
    """
    Normalized contact information with organization context support
    """
    user = ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    organization = ForeignKey(
        IncidentOrganization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Organization context (null = global contact)"
    )
    contact_type = CharField(
        max_length=10,
        choices=[('EMAIL', 'Email'), ('PHONE', 'Phone')]
    )
    value = CharField(max_length=100)
    is_primary = BooleanField(default=False)
    is_active = BooleanField(default=True)  # Soft delete support
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        # Prevent duplicate contacts within same context
        unique_together = [['user', 'organization', 'contact_type', 'value']]
        # Only one primary contact per type per context
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'organization', 'contact_type'],
                condition=Q(is_primary=True, is_active=True),
                name='unique_primary_contact'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['is_primary', 'is_active']),
        ]
```

### Extended UserProfile Model
```python
# Add to existing UserProfile model
use_gravatar = BooleanField(default=True, help_text="Use Gravatar for profile photo")
gravatar_email = EmailField(
    blank=True,
    help_text="Email for Gravatar (defaults to account email)"
)
```

## Implementation Schedule

### Day 1: Database Foundation
**Tasks**:
- Create Contact model with proper constraints
- Extend UserProfile with Gravatar fields
- Create and run migrations
- Update admin interfaces

**Files**:
- `user_profile/models.py` - Add Contact model, extend UserProfile
- `user_profile/admin.py` - Contact admin interface
- `user_profile/migrations/` - Database migrations

### Day 2: Core Utilities & Services
**Tasks**:
- Contact management utility functions
- Gravatar URL generation with fallbacks
- Form validation logic

**Files**:
- `user_profile/utils.py` - Contact and photo utilities
- `user_profile/forms.py` - Contact management forms

### Day 3: Views & Templates
**Tasks**:
- Contact CRUD views
- Update profile templates with contact fields
- Add profile photo display components

**Files**:
- `user_profile/views.py` - Contact management views
- `user_profile/templates/user_profile/contacts.html` - Contact management UI
- `user_profile/templates/components/profile_photo.html` - Reusable photo component

### Day 4: API & Integration
**Tasks**:
- REST API endpoints for contact management
- Integration with operations app templates
- Profile photo display across applications

**Files**:
- `user_profile/serializers.py` - Contact serializers
- `user_profile/api_views.py` - DRF viewsets
- `user_profile/api_urls.py` - API URL patterns
- `operations/templates/operations/` - Updated with profile components

### Day 5: Testing & Polish
**Tasks**:
- Model and view tests
- API endpoint testing
- Basic security access control validation
- Manual workflow testing

**Files**:
- `user_profile/tests.py` - Comprehensive test coverage
- Documentation updates

## Key Functions & Methods

### Contact Management
```python
def get_user_contacts(user, organization=None, contact_type='all'):
    """Retrieve contacts for user in specific organizational context"""

def create_user_contact(user, contact_type, value, organization=None, is_primary=False):
    """Create new contact with validation and constraint checking"""

def get_primary_contact(user, contact_type, organization=None):
    """Get primary contact for user/org/type combination"""
```

### Photo Management
```python
def get_profile_photo_url(user, size=150):
    """Generate profile photo URL with Gravatar fallback to Bootstrap Icons"""

def generate_gravatar_url(email, size=150, default='mp'):
    """Generate secure Gravatar URL with fallback options"""
```

### Template Components
```python
# Template tag for reusable profile photo display
{% load profile_tags %}
{% profile_photo user size=75 css_class="rounded-circle" %}

# Contact display component
{% contact_info user organization=current_org show_phone=True %}
```

## API Endpoints

### Contact Management API
```python
# user_profile/api_urls.py
urlpatterns = [
    path('contacts/', ContactListCreateView.as_view(), name='contact-list'),
    path('contacts/<int:pk>/', ContactDetailView.as_view(), name='contact-detail'),
    path('users/<int:user_id>/contacts/', UserContactListView.as_view(), name='user-contacts'),
]
```

### Authentication & Authorization
- All API endpoints require authentication (`IsAuthenticated`)
- Users can only manage their own contacts
- Organization context filtering based on user membership
- Respect existing public profile visibility settings

## Testing Strategy

### Model Tests
```python
def test_contact_unique_constraints():
    """Test unique constraints prevent duplicate contacts"""

def test_primary_contact_enforcement():
    """Test only one primary contact per type/organization"""

def test_soft_delete_functionality():
    """Test is_active field for soft delete"""
```

### View Tests
```python
def test_contact_crud_operations():
    """Test create, read, update, delete operations"""

def test_organization_context_filtering():
    """Test contacts filtered by organization membership"""

def test_unauthorized_contact_access():
    """Test security controls prevent unauthorized access"""
```

### API Tests
```python
def test_api_authentication_required():
    """Test all endpoints require authentication"""

def test_api_contact_serialization():
    """Test proper data serialization/deserialization"""

def test_api_organization_filtering():
    """Test API respects organization context"""
```

## Integration with Existing Code

### UserProfile Form Integration
```python
# Extend existing UserProfileForm to handle new Gravatar fields
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [..., 'use_gravatar', 'gravatar_email']  # Add new fields
```

### Operations App Integration
```python
# Update operations templates to use profile photo component
{% load profile_tags %}
<div class="user-info">
    {% profile_photo user size=50 %}
    <span>{{ user.get_full_name }}</span>
    {% contact_info user organization=current_org %}
</div>
```

### Existing API Compatibility
- UserRosterAPIView remains unchanged
- New contact API endpoints follow established authentication patterns
- Maintain backward compatibility with existing profile functionality

## Security Considerations

### Access Control
- Contact information respects existing public profile visibility settings
- Organization-based filtering prevents unauthorized contact access
- API endpoints use existing authentication middleware

### Data Validation
```python
# Contact form validation
def clean_value(self):
    value = self.cleaned_data['value']
    contact_type = self.cleaned_data.get('contact_type')

    if contact_type == 'EMAIL':
        validate_email(value)
    elif contact_type == 'PHONE':
        # Basic phone validation
        if not re.match(r'^[\d\-\(\)\s\+\.]+$', value):
            raise ValidationError('Invalid phone number format')

    return value
```

### Input Sanitization
- Django's built-in form validation for email/phone fields
- XSS protection via Django's template auto-escaping
- CSRF protection on all forms

## Success Metrics

### Technical Goals
- Contact CRUD operations complete in <200ms
- Profile photo loading with Gravatar fallback in <1 second
- Zero failed test cases in test suite
- API endpoints return proper HTTP status codes

### User Experience Goals
- Profile completion rate >90% (contacts + photo)
- Contact information displays consistently across all views
- Administrative contact management works without errors
- Profile photos display properly with graceful Gravatar fallbacks

## Deployment Strategy

### Database Migration
- Migrations designed for zero-downtime deployment
- Contact model indexes created concurrently
- UserProfile fields added with safe defaults

### Rollout Process
1. Deploy models and migrations
2. Deploy admin interfaces for contact management
3. Deploy user-facing contact forms and views
4. Deploy API endpoints and operations integration
5. Monitor for performance or usability issues

## Future Enhancement Proposals

*The following features were removed from current scope to focus on rapid MVP delivery. Each has been documented as a separate proposal for future implementation:*

### Messaging System
**Scope**: Dedicated messaging app with WebSocket real-time delivery
**Effort**: 4 weeks
**File**: `plans/messaging-system-proposal.md`

### Notification Infrastructure
**Scope**: Complete notification system with email templates and in-app center
**Effort**: 4 weeks
**File**: `plans/notification-system-proposal.md`

### Photo Management Pipeline
**Scope**: Upload processing with cloud storage and admin moderation
**Effort**: 4 weeks
**File**: `plans/photo-management-proposal.md`

## Conclusion

This finalized plan delivers essential user profile enhancements as a 1-week MVP while maintaining architectural integrity for future expansion. The normalized Contact model and Gravatar integration provide immediate value without technical debt accumulation.

The three future proposals ensure that advanced features (messaging, notifications, photo uploads) can be implemented with proper architecture when organizational priorities and timelines allow for more comprehensive development phases.

**Next Steps:**
1. Review and approve this final plan
2. Begin Day 1 implementation with database foundation
3. Prioritize future proposals based on user feedback and operational needs

*This plan balances rapid MVP delivery with long-term architectural sustainability for NetEOC's disaster response mission.*
