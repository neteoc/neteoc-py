from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from operations.models import Incident, CheckIn


class Command(BaseCommand):
    help = "Create incident access groups with appropriate permissions"

    def handle(self, *args, **options):
        """Create the incident access groups"""

        # Get content types
        incident_ct = ContentType.objects.get_for_model(Incident)
        checkin_ct = ContentType.objects.get_for_model(CheckIn)

        # Define group configurations
        group_configs = [
            {
                "name": "Incident Admins",
                "description": "Full control over incidents and check-ins",
                "permissions": [
                    "add_incident",
                    "change_incident",
                    "delete_incident",
                    "view_incident",
                    "add_checkin",
                    "change_checkin",
                    "delete_checkin",
                    "view_checkin",
                ],
            },
            {
                "name": "Incident Responders",
                "description": "Can check-in/out people, view incidents",
                "permissions": [
                    "view_incident",
                    "add_checkin",
                    "change_checkin",
                    "view_checkin",
                ],
            },
            {
                "name": "Incident Viewers",
                "description": "Read-only access to incidents and check-ins",
                "permissions": [
                    "view_incident",
                    "view_checkin",
                ],
            },
        ]

        # Create groups and assign permissions
        for config in group_configs:
            self._create_group_with_permissions(config, incident_ct, checkin_ct)

        self._display_success_message()

    def _create_group_with_permissions(self, config, incident_ct, checkin_ct):
        """Create a group and assign its permissions"""
        group, created = Group.objects.get_or_create(name=config["name"])

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created '{config['name']}' group"))
        else:
            self.stdout.write(f"'{config['name']}' group already exists")

        # Add permissions to group
        for perm_codename in config["permissions"]:
            self._add_permission_to_group(group, perm_codename, incident_ct, checkin_ct)

    def _add_permission_to_group(self, group, perm_codename, incident_ct, checkin_ct):
        """Add a specific permission to a group"""
        try:
            content_type = incident_ct if perm_codename.endswith("incident") else checkin_ct
            permission = Permission.objects.get(content_type=content_type, codename=perm_codename)
            group.permissions.add(permission)
        except Permission.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Permission {perm_codename} not found"))

    def _display_success_message(self):
        """Display success message with group descriptions"""
        self.stdout.write(self.style.SUCCESS("\nIncident access groups created successfully!"))
        self.stdout.write("\nGroup descriptions:")
        self.stdout.write("- Incident Admins: Full control over incidents and check-ins")
        self.stdout.write("- Incident Responders: Can check-in/out people, view incidents")
        self.stdout.write("- Incident Viewers: Read-only access to incidents and check-ins")
        self.stdout.write("\nUse Django admin to assign users to these groups.")
