# Incident Ownership and Access Control

This document describes the incident ownership and group-based access control system implemented in the operations app.

## Overview

The system provides fine-grained access control for incidents and check-ins based on:

1. **Incident Ownership** - Each incident has an owner who has full control
2. **Group-based Permissions** - Users can be assigned to groups with different access levels

## Incident Ownership

### Owner Field

- Each incident now has a required `owner` field referencing a User
- The owner has full administrative control over the incident
- When creating a new incident, the current user is automatically set as the owner
- The owner can be changed in the Django admin interface

### Owner Permissions

Incident owners have the following permissions:

- Full read/write access to the incident
- Can modify incident details (name, type, status, etc.)
- Can delete the incident
- Can view and modify all check-ins for the incident
- Can delete check-ins for the incident

## Group-based Access Control

### Available Groups

The system defines three permission groups that can be assigned to users:

#### 1. Incident Admins

- **Full Control**: Complete access to all incidents and check-ins
- **Permissions**: Can create, view, edit, and delete incidents and check-ins
- **Use Case**: Emergency management coordinators, supervisors

#### 2. Incident Responders

- **Write Access**: Can check-in/out people and view incidents
- **Permissions**: Can create and edit check-ins, view all incidents
- **Restrictions**: Cannot create, edit, or delete incidents
- **Use Case**: Field responders, volunteers who need to check people in/out

#### 3. Incident Viewers

- **Read-only Access**: Can view incidents and check-ins but cannot modify anything
- **Permissions**: View-only access to incidents and check-ins
- **Use Case**: Observers, reporters, stakeholders who need visibility

### Setting Up Groups

Run the management command to create the groups:

```bash
uv run python manage.py setup_incident_groups
```

Then assign users to groups through the Django admin interface:

1. Go to Admin → Authentication and Authorization → Users
2. Edit a user
3. In the "Permissions" section, add them to the appropriate groups

## Access Control Logic

### Permission Hierarchy

1. **Superusers and Staff**: Always have full access to everything
2. **Incident Owners**: Full access to their owned incidents
3. **Group Members**: Access based on group permissions
4. **Other Users**: No access (unless they own the incident)

### View Filtering

- Users only see incidents they have access to based on ownership or group membership
- Check-ins are filtered based on the underlying incident permissions
- The operations dashboard shows only accessible incidents and their statistics

### Permission Checking Methods

The Incident model provides helper methods for checking permissions:

```python
# Check if user has admin access (can edit/delete incident)
incident.has_admin_access(user)

# Check if user has read access (can view incident details)
incident.has_read_access(user)

# Check if user has write access (can create/edit check-ins)
incident.has_write_access(user)
```

## Admin Interface Integration

### Incident Admin

- Shows owner in list view and filter options
- Automatically sets owner to current user when creating new incidents
- Filters incidents based on user permissions
- Respects ownership for edit/delete permissions

### CheckIn Admin

- Filters check-ins based on incident access permissions
- Respects incident permissions for edit/delete operations
- Shows incident ownership information

## Templates and UI

### Dashboard Updates

- Displays incident owner information
- Shows only incidents the user has access to
- Filters statistics based on accessible incidents

### Permission-aware Navigation

- Quick check-in dropdown only shows incidents user can write to
- Create incident links only available to users with appropriate permissions

## Migration and Data

### Database Changes

- Added `owner` field to Incident model (required, foreign key to User)
- Created data migration to set existing incidents' owners
- Maintains backward compatibility with existing data

### Group Setup

- Management command creates the three permission groups
- Assigns appropriate Django permissions to each group
- Can be run multiple times safely (idempotent)

## Security Considerations

### Access Control

- All views check permissions before allowing access
- Django admin respects the custom permission logic
- Database queries are filtered at the ORM level
- No incidents are exposed to unauthorized users

### Permission Validation

- Users cannot access incidents they don't own or lack group access to
- Check-in creation requires write access to the associated incident
- Admin operations require admin access to the specific incident

## Usage Examples

### Setting up a new emergency response team:

1. Create incidents and assign appropriate owners
2. Add field responders to the "Incident Responders" group
3. Add coordinators to the "Incident Admins" group
4. Add observers to the "Incident Viewers" group

### Managing incident ownership:

1. Incident creator automatically becomes the owner
2. Ownership can be transferred via Django admin
3. Original creator remains in `created_by` field for audit trail

This system provides flexible, role-based access control while maintaining the security principle of least privilege access.
