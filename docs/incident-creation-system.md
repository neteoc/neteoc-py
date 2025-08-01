# Incident Creation System

This document describes the incident creation system that allows authorized users to create new incidents through a web interface.

## Overview

The incident creation system provides a user-friendly web interface for creating and managing incidents, replacing the need to use the Django admin interface for basic incident creation.

## Features

### 1. Web-based Incident Creation

- **URL**: `/operations/incident/create/`
- **Purpose**: Allow authorized users to create new incidents through a form interface
- **Access Control**: Limited to superusers, staff, and users in the "Incident Admins" group

### 2. Incident Detail Pages

- **URL**: `/operations/incident/<incident_id>/`
- **Purpose**: Display comprehensive incident information including incident commander details
- **Features**:
  - Incident status and metadata
  - Incident commander contact information (if assigned)
  - Recent check-ins
  - Statistics (active/total check-ins)
  - Quick action buttons based on user permissions

### 3. Incident Commander Field

- Added `incident_commander` field to the Incident model
- Optional field that designates the primary point of contact for the incident
- Displayed prominently on the incident detail page
- Separate from the `owner` field (which controls permissions)

## Form Fields

The incident creation form includes:

### Required Fields

- **Name**: Descriptive name for the incident
- **Incident Type**: Dropdown with predefined types (Hurricane, Flood, etc.)
- **Status**: Active, Standby, or Closed
- **Start Date**: When the incident began or is scheduled to begin

### Optional Fields

- **Description**: Additional details about the incident
- **End Date**: When the incident ended (for closed incidents)
- **Location**: Primary location of the incident
- **Incident Commander**: User designated as primary contact

## Access Control

### Creation Permissions

Users can create incidents if they are:

- Superusers
- Staff members
- Members of the "Incident Admins" group

### Automatic Field Assignment

When creating an incident:

- `owner` is automatically set to the current user
- `created_by` is automatically set to the current user
- User gains full administrative control over the incident

## User Interface

### Dashboard Integration

- "Create Incident" button appears in the dashboard header for authorized users
- Incident cards link to detailed incident pages
- Quick action buttons provide easy access to common functions

### Navigation

- Breadcrumb navigation from incident pages back to dashboard
- Contextual action buttons based on user permissions
- Clear visual status indicators

### Responsive Design

- Mobile-friendly forms and layouts
- Bootstrap 5 styling for consistency
- Clear visual hierarchy and intuitive workflows

## Incident Detail Page Features

### Information Display

- Incident metadata (type, status, dates, location)
- Owner and incident commander information
- Activity statistics
- Recent check-ins table

### Incident Commander Section

- Dedicated card showing commander information
- Name, email, and contact details
- Clearly labeled as "Primary Point of Contact"
- Avatar placeholder for visual appeal

### Quick Actions

Based on user permissions:

- **Can Check-in**: "Check In Person" button (for active incidents)
- **Can View**: "View Report" and "Details" links
- **Can Edit**: "Edit Incident" link to admin interface

### Status Indicators

- Color-coded alerts based on incident status
- Active incidents show green "accepting check-ins" message
- Standby/Closed incidents show appropriate warnings

## Implementation Details

### Models

```python
class Incident(models.Model):
    # ... existing fields ...
    incident_commander = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commanded_incidents",
        help_text="The incident commander - primary point of contact"
    )
```

### Views

- `create_incident()`: Handles incident creation form
- `incident_detail()`: Displays incident information with permission checks
- Integrated with existing permission system

### Templates

- `operations/incident/create.html`: Incident creation form
- `operations/incident/detail.html`: Incident detail page
- Updated dashboard with creation button and detail links

### URLs

- `/operations/incident/create/` - Create new incident
- `/operations/incident/<id>/` - View incident details

## Security

### Permission Checks

- Creation limited to authorized users only
- Detail page respects existing incident access controls
- Admin interface integration maintains security model

### Data Validation

- Form validation ensures required fields
- Date validation for start/end dates
- User selection limited to active users for incident commander

## Integration

### Django Admin

- Updated admin interface includes incident commander field
- Maintains existing functionality while adding web creation option
- Admin remains available for advanced editing

### Existing Systems

- Fully integrated with existing permission system
- Maintains compatibility with check-in system
- Respects ownership and group-based access controls

## Usage Examples

### Creating an Incident

1. Navigate to Operations Dashboard
2. Click "Create Incident" button (if authorized)
3. Fill out incident information form
4. Optionally assign an incident commander
5. Submit to create the incident

### Viewing Incident Details

1. Click incident name or "Details" button from dashboard
2. View comprehensive incident information
3. See incident commander contact details
4. Access quick action buttons based on permissions

This system provides a complete incident management workflow while maintaining security and integrating seamlessly with existing operations functionality.
