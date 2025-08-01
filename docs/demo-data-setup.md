# Demo Data Setup

This document explains how to set up demonstration data for NetEOC.

## Overview

The `setup_demo_data` management command creates a complete set of sample data to demonstrate NetEOC's capabilities, including:

- 4 sample organizations (Emergency Management, State Defense Force, Fire Department, Medical Center)
- 8 demo users with various roles and cross-organization memberships
- 4 sample incidents (active hurricane response, support mission, upcoming festival, completed training)
- 3 support requests with different statuses
- Sample check-ins for the active hurricane incident

## Usage

### Basic Setup

To create demo data:

```bash
uv run python manage.py setup_demo_data
```

### Clear and Recreate

To clear existing demo data and create fresh data:

```bash
uv run python manage.py setup_demo_data --clear
```

## Demo Users

All demo users have the password: `demo123`

| Username | Organizations | Role | Description |
|----------|---------------|------|-------------|
| john.smith | Demo County EMA | Admin | EMA Administrator |
| sarah.johnson | Demo County EMA | Incident Manager | EMA Incident Manager |
| mike.wilson | Demo State Defense Force | Admin | SDF Administrator |
| lisa.chen | Demo State Defense Force | Incident Manager | SDF Incident Manager |
| david.brown | Demo City Fire Dept | Admin | Fire Department Admin |
| jennifer.garcia | Demo City Fire Dept | Responder | Fire Department Responder |
| robert.martinez | Demo Regional Medical | Admin | Medical Center Admin |
| maria.rodriguez | EMA + Medical | Responder/Viewer | Cross-organization user |

### Superuser Integration

The initial superuser (user ID 1) is automatically added to:

- **Owner** of Demo County Emergency Management Agency
- **Member** of Demo State Defense Force

This demonstrates the organization ownership and multi-organization membership features.

## Demo Organizations

1. **Demo County Emergency Management** - Primary emergency management agency
2. **Demo State Defense Force** - State-level support organization
3. **Demo City Fire Department** - Local fire department
4. **Demo Regional Medical Center** - Medical/EMS services

## Demo Incidents

### Active Incidents

- **Demo Hurricane Response 2025** (EMA) - Active hurricane response
- **Demo Hurricane - SDF Support** (SDF) - Supporting incident from State Defense Force

### Upcoming Incidents

- **Demo Community Festival 2025** (Fire Dept) - Standby for upcoming festival

### Completed Incidents

- **Demo Flood Response Training** (EMA) - Closed training exercise

## Demo Support Requests

1. **Approved**: EMA requesting personnel support from SDF for hurricane response
2. **Pending**: Fire Department requesting medical support for festival
3. **Pending**: EMA requesting fire department support for hurricane shelters

## Demo Features Demonstrated

- **Multi-organization coordination** - Multiple agencies working together
- **Support request workflow** - Requesting and approving inter-agency support
- **Incident management** - Active and completed incidents
- **User role management** - Different permission levels within organizations
- **Cross-organization membership** - Users belonging to multiple agencies
- **Check-in tracking** - Personnel accountability during incidents
- **Organization ownership** - Administrative control over organizations

## Testing Scenarios

After setting up demo data, you can test:

1. **Organization switching** - Log in as maria.rodriguez and switch between organizations
2. **Support request workflow** - Review pending requests and approve/decline them
3. **Incident management** - Create new incidents, update existing ones
4. **Check-in/out process** - Add new check-ins to active incidents
5. **Multi-organization coordination** - See how incidents link between organizations

## Cleanup

To remove all demo data:

```bash
uv run python manage.py setup_demo_data --clear
```

This will remove all demo organizations, users, incidents, support requests, and check-ins while preserving any real data.
