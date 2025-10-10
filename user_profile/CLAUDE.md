# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this folder.

## Folder Overview

The `user_profile` app manages extended user profiles for disaster response personnel, including roster IDs, addresses with geographic coordinates, and public profile information for inter-organization coordination.

## Core Models

### `Address` Model
- **Purpose**: Normalized address storage with coordinate support for emergency response
- **Key Features**:
  - Standard address fields (street_1, street_2, city, state, zip_code)
  - Geographic coordinates (latitude/longitude) with accuracy tracking
  - Distance calculation methods using Haversine formula
  - Geocoding metadata (source, timestamp)
  - Ready for GeoDjango Point field migration when spatial database is configured
- **Methods**: `get_distance_to()`, `is_within_radius()`, `set_coordinates()`
- **Usage**: Reusable across the application for any location-based functionality

### `UserProfile` Model
- **Purpose**: Extended user information for disaster response operations
- **Key Fields**:
  - `roster_id`: 3-letter + 4-digit format (e.g., DOE1234) for quick check-in identification
  - `drivers_license_id`: Official identification
  - `address`: ForeignKey to Address model for normalized address storage
  - Public profile fields with granular visibility controls
- **Auto-creation**: Django signals automatically create/save profiles for all users
- **Integration**: Links with operations app for organization membership display

## Forms Architecture

### `UserProfileForm`
- **Complex Form**: Handles both UserProfile and Address data in single form
- **Address Logic**: Creates/updates Address instances with coordinate handling
- **Validation**: Roster ID format (ABC1234), state abbreviations, ZIP codes
- **Save Method**: Custom save logic coordinating UserProfile and Address creation/updates

### `PublicUserProfileForm`
- **Purpose**: Separate form for public-facing profile information
- **Fields**: Bio, phone, email with individual visibility controls
- **Security**: Only displays information based on visibility settings

## API Endpoints

### `UserRosterAPIView` (DRF)
- **Purpose**: Provides user roster data for check-in form auto-population
- **Security**: Requires authentication, includes access logging
- **Data**: Returns id, first_name, last_name, roster_id (safe user data only)
- **Integration**: Used by operations app check-in forms via AJAX

## Views & Access Control

### `profile` View
- **Dual Forms**: Handles both profile and public profile forms on single page
- **Organization Display**: Shows user's organization memberships with roles
- **Form Type Detection**: Uses hidden field to determine which form was submitted

### `view_public_profile` View
- **Access Control**: Multi-layered security
  - Users can view their own profiles
  - Organization members can view each other's profiles
  - Users checked into incidents can view commander profiles
  - Respects public_visible setting
- **Security**: Returns 404 for unauthorized access (no information leakage)

## Templates

### `profile.html`
- **Bootstrap 5**: Responsive design with card-based layout
- **Dual Forms**: Profile information and public profile in separate cards
- **Organization Display**: Shows memberships with role badges
- **Help Section**: Comprehensive guidance on roster ID format, coordinates, etc.
- **Real-time Feedback**: Displays current values and validation errors

## Key Integrations

1. **Operations App**:
   - Displays organization memberships
   - API used for check-in auto-population
   - Access control based on incident relationships

2. **Address Reusability**:
   - Designed for reuse across incidents, assets, organizations
   - Geographic coordinate support for emergency response mapping

3. **Security Architecture**:
   - All views require `@login_required`
   - API endpoints with DRF authentication
   - Granular visibility controls for public information

## Development Guidelines

### Address Handling
- Always use Address model for location data (don't store addresses as text)
- Handle coordinate data carefully (longitude/latitude order)
- Consider geocoding accuracy levels when working with coordinates

### Form Development
- Use existing validation patterns for roster IDs, states, ZIP codes
- Coordinate Address creation/updates through UserProfileForm patterns
- Implement proper error handling for address operations

### API Development
- Follow existing security patterns (authentication, logging)
- Return minimal necessary data (don't expose sensitive information)
- Use serializers for consistent data formatting

### Access Control
- Always implement proper authorization checks
- Use organization membership patterns for access control
- Return 404 (not 403) to prevent information leakage

## Testing

- Comprehensive API tests in `tests.py`
- Tests cover authentication, data retrieval, error handling
- Test both users with and without profiles
- API endpoint testing includes authentication requirements

## Future Considerations

- Ready for GeoDjango migration (Address.latitude/longitude → PointField)
- Address model designed for spatial queries when PostGIS is fully configured
- Public profile system ready for expanded inter-organization workflows
