Template Syntax Errors Breaking Operations Check-in System

Assignees: @Copilot
Labels: bug, high-priority, templates
Milestone:
Projects:

## Issue Summary

Multiple template syntax errors are preventing the operations check-in system from loading, causing 500 Internal Server Errors when users try to access `/operations/checkin/`.

## Problem Description

During user profile system testing, two distinct template issues were discovered that prevent critical emergency response functionality from working:

1. **TemplateSyntaxError**: Malformed template tag concatenation in check-in report template
2. **TemplateDoesNotExist**: Incorrect base template reference in user profile contacts template

## Error Details

### Error 1: Template Tag Concatenation Issue
**Location**: `operations/templates/operations/checkin/report.html` lines 36 and 38
**Error Message**: `TemplateSyntaxError: Could not parse the remainder: '"{%' from '"{%'`

**Problematic Code**:
```django
{% url 'operations:checkin_report' as report_url %}{% bootstrap_button button_type="link" content=incident.name button_class="btn-primary active" href=report_url|add:"?incident="|add:incident.id %}
```

**Issue**: Multiple template tags are concatenated on a single line without proper separation, causing Django's template parser to fail.

### Error 2: Missing Base Template
**Location**: `user_profile/templates/user_profile/contacts.html` line 1
**Error Message**: `TemplateDoesNotExist: theme/base.html`

**Problematic Code**:
```django
{% extends "theme/base.html" %}
```

**Issue**: Template references `theme/base.html` but the correct base template in this project is `base.html` (located at `theme/templates/base.html`).

## Steps to Reproduce

1. Start the Django development server: `uv run python manage.py runserver`
2. Log in as any user
3. Navigate to `/operations/checkin/`
4. **Expected**: Check-in dashboard loads
5. **Actual**: 500 Internal Server Error with template syntax error

**Alternative reproduction for contacts error**:
1. Navigate to `/profile/contacts/`
2. **Expected**: User contacts page loads
3. **Actual**: 500 Internal Server Error with TemplateDoesNotExist

## Impact

- **Severity**: High - Blocks critical emergency response functionality
- **Users Affected**: All users trying to access check-in system
- **Business Impact**: Prevents personnel from checking into incidents during emergencies

## Root Cause Analysis

1. **Template Tag Issue**: The bootstrap button template tags were likely copy-pasted or auto-generated without proper line breaks, causing Django's template parser to treat them as a single malformed expression.

2. **Base Template Issue**: Inconsistent template inheritance - some templates use `base.html` while others use `theme/base.html`, but only `base.html` exists in the correct template directory structure.

## Proposed Solution

### Fix 1: Separate Template Tags (Critical)
In `operations/templates/operations/checkin/report.html`, replace lines 36 and 38:

**Current**:
```django
{% url 'operations:checkin_report' as report_url %}{% bootstrap_button button_type="link" content=incident.name button_class="btn-primary active" href=report_url|add:"?incident="|add:incident.id %}
```

**Fixed**:
```django
{% url 'operations:checkin_report' as report_url %}
{% bootstrap_button button_type="link" content=incident.name button_class="btn-primary active" href=report_url|add:"?incident="|add:incident.id %}
```

Repeat the same fix for line 38 with the outline button.

### Fix 2: Correct Base Template Reference
In `user_profile/templates/user_profile/contacts.html`, change line 1:

**Current**:
```django
{% extends "theme/base.html" %}
```

**Fixed**:
```django
{% extends "base.html" %}
```

## Testing Instructions

After applying fixes:

1. Start development server: `uv run python manage.py runserver`
2. Test check-in system:
   - Navigate to `/operations/checkin/`
   - Verify the incident filter buttons work correctly
   - Check that page loads without errors
3. Test contacts page:
   - Navigate to `/profile/contacts/`
   - Verify page loads without template errors

## Additional Context

- **Django Version**: 5.2.4
- **Template Engine**: Django Templates (not Jinja2)
- **Bootstrap Integration**: django-bootstrap5 package
- **Environment**: Development server on Ubuntu/Linux

## Files to Modify

1. `operations/templates/operations/checkin/report.html` (lines 36, 38)
2. `user_profile/templates/user_profile/contacts.html` (line 1)

## Verification

The following log entries should disappear after fixes:
```
django.template.exceptions.TemplateSyntaxError: Could not parse the remainder: '"{%' from '"{%'
django.template.exceptions.TemplateDoesNotExist: theme/base.html
```

And these requests should return 200 OK instead of 500:
- `GET /operations/checkin/`
- `GET /profile/contacts/`

---

**Priority**: High
**Type**: Bug
**Component**: Templates
**Affects**: Emergency Response Operations
