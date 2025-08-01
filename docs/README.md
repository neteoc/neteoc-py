# Documentation

This directory contains comprehensive documentation for the NetEOC disaster response application.

## Table of Contents

### System Architecture

- [Django Organizations Cookbook](django-orgs-cookbook.md) - Guide for implementing multi-organization features using django-organizations

### Core Features

- [Incident Creation System](incident-creation-system.md) - Documentation for creating and managing incidents
- [Incident Ownership and Access Control](incident-ownership-and-access-control.md) - Access control and permission systems for incidents

### Implementation Guides

- [Organization Switching Implementation](organization-switching-implementation.md) - Multi-organization context switching functionality
- [Support Request Implementation](support-request-implementation.md) - Inter-organization support request workflow
- [Enhanced Footer Implementation](enhanced-footer-implementation.md) - Context-aware footer with organization and incident information
- [Demo Data Setup](demo-data-setup.md) - Guide for setting up demonstration data

### Deployment

- [Docker Deployment](docker-deployment.md) - Guide for deploying NetEOC using Docker containers with automatic migrations

## Getting Started

For getting started with the project, see the main [README.md](../README.md) in the root directory.

## Contributing

When adding new documentation:

1. Place all documentation files in this `docs` directory
2. Use markdown (.md) format for all documentation
3. Update this table of contents when adding new documents
4. Follow the project's [coding standards](../.github/copilot-instructions.md#code-style-and-standards)
