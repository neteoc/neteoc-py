from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from operations.models import (
    IncidentOrganization,
    IncidentOrganizationUser,
    Incident,
    SupportRequest,
    CheckIn,
)


class Command(BaseCommand):
    help = "Create sample data for NetEOC demonstration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing demo data before creating new data",
        )

    def handle(self, *args, **options):
        """Create sample data for demonstration"""

        if options["clear"]:
            self._clear_demo_data()

        self.stdout.write("Creating demonstration data for NetEOC...")

        # Create sample organizations
        organizations = self._create_organizations()

        # Create sample users
        users = self._create_users(organizations)

        # Add superuser to organizations
        self._add_superuser_to_organizations(organizations)

        # Create sample incidents
        incidents = self._create_incidents(organizations, users)

        # Create sample support requests
        self._create_support_requests(organizations, users, incidents)

        # Create sample check-ins
        self._create_checkins(incidents, users)

        self._display_summary()

    def _clear_demo_data(self):
        """Clear existing demo data"""
        self.stdout.write("Clearing existing demo data...")

        # Delete in order to respect foreign key constraints
        CheckIn.objects.filter(incident__name__contains="Demo").delete()
        SupportRequest.objects.filter(title__contains="Demo").delete()
        Incident.objects.filter(name__contains="Demo").delete()

        # Delete demo users (but keep admin users)
        demo_users = User.objects.filter(
            username__in=[
                "john.smith",
                "sarah.johnson",
                "mike.wilson",
                "lisa.chen",
                "david.brown",
                "jennifer.garcia",
                "robert.martinez",
                "maria.rodriguez",
            ]
        )
        demo_users.delete()

        # Delete demo organizations
        IncidentOrganization.objects.filter(name__contains="Demo").delete()

        self.stdout.write(self.style.SUCCESS("Demo data cleared"))

    def _create_organizations(self):
        """Create sample organizations"""
        self.stdout.write("Creating sample organizations...")

        org_configs = [
            {
                "name": "Demo County Emergency Management",
                "type": "EMERGENCY_MGMT",
                "contact_email": "ema@democounty.gov",
                "contact_phone": "(555) 123-4567",
                "address": "123 Emergency Way, Demo City, FL 12345",
                "website": "https://democounty.gov/ema",
            },
            {
                "name": "Demo State Defense Force",
                "type": "STATE",
                "contact_email": "operations@demosdf.mil",
                "contact_phone": "(555) 987-6543",
                "address": "456 Military Base Rd, Demo City, FL 12346",
                "website": "https://demosdf.mil",
            },
            {
                "name": "Demo City Fire Department",
                "type": "FIRE",
                "contact_email": "chief@democityfd.org",
                "contact_phone": "(555) 555-0123",
                "address": "789 Fire Station Ave, Demo City, FL 12347",
                "website": "https://democityfd.org",
            },
            {
                "name": "Demo Regional Medical Center",
                "type": "EMS",
                "contact_email": "emergency@demomedical.org",
                "contact_phone": "(555) 555-0456",
                "address": "321 Hospital Blvd, Demo City, FL 12348",
                "website": "https://demomedical.org",
            },
        ]

        organizations = {}
        for config in org_configs:
            org, created = IncidentOrganization.objects.get_or_create(
                name=config["name"],
                defaults={
                    "organization_type": config["type"],
                    "contact_email": config["contact_email"],
                    "contact_phone": config["contact_phone"],
                    "address": config["address"],
                    "website": config["website"],
                    "is_verified": True,
                    "is_active": True,
                },
            )
            organizations[config["type"]] = org

            if created:
                self.stdout.write(f"  ✓ Created {org.name}")
            else:
                self.stdout.write(f"  → {org.name} already exists")

        return organizations

    def _create_users(self, organizations):
        """Create sample users and assign them to organizations"""
        self.stdout.write("Creating sample users...")

        user_configs = [
            {
                "username": "john.smith",
                "email": "john.smith@democounty.gov",
                "first_name": "John",
                "last_name": "Smith",
                "organizations": ["EMERGENCY_MGMT"],
                "roles": ["ADMIN"],
            },
            {
                "username": "sarah.johnson",
                "email": "sarah.johnson@democounty.gov",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "organizations": ["EMERGENCY_MGMT"],
                "roles": ["INCIDENT_MANAGER"],
            },
            {
                "username": "mike.wilson",
                "email": "mike.wilson@demosdf.mil",
                "first_name": "Mike",
                "last_name": "Wilson",
                "organizations": ["STATE"],
                "roles": ["ADMIN"],
            },
            {
                "username": "lisa.chen",
                "email": "lisa.chen@demosdf.mil",
                "first_name": "Lisa",
                "last_name": "Chen",
                "organizations": ["STATE"],
                "roles": ["INCIDENT_MANAGER"],
            },
            {
                "username": "david.brown",
                "email": "david.brown@democityfd.org",
                "first_name": "David",
                "last_name": "Brown",
                "organizations": ["FIRE"],
                "roles": ["ADMIN"],
            },
            {
                "username": "jennifer.garcia",
                "email": "jennifer.garcia@democityfd.org",
                "first_name": "Jennifer",
                "last_name": "Garcia",
                "organizations": ["FIRE"],
                "roles": ["RESPONDER"],
            },
            {
                "username": "robert.martinez",
                "email": "robert.martinez@demomedical.org",
                "first_name": "Robert",
                "last_name": "Martinez",
                "organizations": ["EMS"],
                "roles": ["ADMIN"],
            },
            {
                "username": "maria.rodriguez",
                "email": "maria.rodriguez@demomedical.org",
                "first_name": "Maria",
                "last_name": "Rodriguez",
                "organizations": ["EMS", "EMERGENCY_MGMT"],  # Cross-organization user
                "roles": ["RESPONDER", "VIEWER"],
            },
        ]

        users = {}
        for config in user_configs:
            user, created = User.objects.get_or_create(
                username=config["username"],
                defaults={
                    "email": config["email"],
                    "first_name": config["first_name"],
                    "last_name": config["last_name"],
                    "is_active": True,
                },
            )

            if created:
                user.set_password("demo123")  # Simple password for demo
                user.save()
                self.stdout.write(f"  ✓ Created user {user.username}")
            else:
                self.stdout.write(f"  → User {user.username} already exists")

            users[config["username"]] = user

            # Add user to organizations
            for i, org_type in enumerate(config["organizations"]):
                org = organizations[org_type]
                role = config["roles"][i] if i < len(config["roles"]) else config["roles"][0]

                org_user, created = IncidentOrganizationUser.objects.get_or_create(
                    organization=org,
                    user=user,
                    defaults={
                        "role": role,
                        "is_admin": role == "ADMIN",
                        "can_create_incidents": role in ["ADMIN", "INCIDENT_MANAGER"],
                        "can_manage_users": role == "ADMIN",
                    },
                )

        return users

    def _add_superuser_to_organizations(self, organizations):
        """Add the initial superuser to organizations"""
        try:
            # Get the first superuser (user ID 1)
            superuser = User.objects.filter(is_superuser=True, id=1).first()

            if not superuser:
                self.stdout.write(
                    self.style.WARNING(
                        "No superuser with ID 1 found, skipping superuser organization setup"
                    )
                )
                return

            self.stdout.write(f"Adding superuser '{superuser.username}' to organizations...")

            # Make superuser an owner of Emergency Management Agency
            ema_org = organizations["EMERGENCY_MGMT"]
            from operations.models import IncidentOrganizationOwner

            owner, created = IncidentOrganizationOwner.objects.get_or_create(
                organization=ema_org, defaults={"organization_user": None}
            )

            # Create organization user relationship for owner
            org_user, created = IncidentOrganizationUser.objects.get_or_create(
                organization=ema_org,
                user=superuser,
                defaults={
                    "role": "ADMIN",
                    "is_admin": True,
                    "can_create_incidents": True,
                    "can_manage_users": True,
                },
            )

            # Update the owner relationship
            if not owner.organization_user:
                owner.organization_user = org_user
                owner.save()

            if created:
                self.stdout.write(f"  ✓ Made {superuser.username} owner of {ema_org.name}")
            else:
                self.stdout.write(f"  → {superuser.username} is already owner of {ema_org.name}")

            # Make superuser a member of State Defense Force
            sdf_org = organizations["STATE"]
            sdf_org_user, created = IncidentOrganizationUser.objects.get_or_create(
                organization=sdf_org,
                user=superuser,
                defaults={
                    "role": "ADMIN",
                    "is_admin": True,
                    "can_create_incidents": True,
                    "can_manage_users": False,  # Not full admin rights in this org
                },
            )

            if created:
                self.stdout.write(f"  ✓ Made {superuser.username} member of {sdf_org.name}")
            else:
                self.stdout.write(f"  → {superuser.username} is already member of {sdf_org.name}")

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Error setting up superuser organizations: {e}"))

    def _create_incidents(self, organizations, users):
        """Create sample incidents"""
        self.stdout.write("Creating sample incidents...")

        now = timezone.now()

        incident_configs = [
            {
                "name": "Demo Hurricane Response 2025",
                "type": "HURRICANE",
                "description": "Category 3 hurricane making landfall in Demo County. Coordinated multi-agency response required.",
                "status": "ACTIVE",
                "organization": organizations["EMERGENCY_MGMT"],
                "owner": users["john.smith"],
                "commander": users["sarah.johnson"],
                "start_date": now - timedelta(days=2),
                "location": "Demo County, Florida",
            },
            {
                "name": "Demo Hurricane - SDF Support",
                "type": "HURRICANE",
                "description": "State Defense Force support mission for Demo County hurricane response.",
                "status": "ACTIVE",
                "organization": organizations["STATE"],
                "owner": users["mike.wilson"],
                "commander": users["lisa.chen"],
                "start_date": now - timedelta(days=1),
                "location": "Demo County, Florida",
            },
            {
                "name": "Demo Community Festival 2025",
                "type": "FESTIVAL",
                "description": "Annual Demo City Summer Festival - medical and safety support required.",
                "status": "STANDBY",
                "organization": organizations["FIRE"],
                "owner": users["david.brown"],
                "commander": users["jennifer.garcia"],
                "start_date": now + timedelta(days=30),
                "end_date": now + timedelta(days=32),
                "location": "Demo City Central Park",
            },
            {
                "name": "Demo Flood Response Training",
                "type": "TRAINING",
                "description": "Multi-agency flood response training exercise.",
                "status": "CLOSED",
                "organization": organizations["EMERGENCY_MGMT"],
                "owner": users["john.smith"],
                "commander": users["sarah.johnson"],
                "start_date": now - timedelta(days=15),
                "end_date": now - timedelta(days=14),
                "location": "Demo County Training Facility",
            },
        ]

        incidents = {}
        for config in incident_configs:
            incident, created = Incident.objects.get_or_create(
                name=config["name"],
                defaults={
                    "incident_type": config["type"],
                    "description": config["description"],
                    "status": config["status"],
                    "organization": config["organization"],
                    "owner": config["owner"],
                    "incident_commander": config["commander"],
                    "start_date": config["start_date"],
                    "end_date": config.get("end_date"),
                    "location": config["location"],
                    "created_by": config["owner"],
                },
            )
            incidents[config["name"]] = incident

            if created:
                self.stdout.write(f"  ✓ Created incident: {incident.name}")
            else:
                self.stdout.write(f"  → Incident already exists: {incident.name}")

        return incidents

    def _create_support_requests(self, organizations, users, incidents):
        """Create sample support requests"""
        self.stdout.write("Creating sample support requests...")

        now = timezone.now()

        request_configs = [
            {
                "title": "Demo Hurricane - Personnel Support Request",
                "description": "Need 20 additional personnel for search and rescue operations during hurricane response.",
                "urgency": "HIGH",
                "requesting_org": organizations["EMERGENCY_MGMT"],
                "target_org": organizations["STATE"],
                "incident": incidents["Demo Hurricane Response 2025"],
                "requested_by": users["sarah.johnson"],
                "status": "APPROVED",
                "start_date": now + timedelta(hours=6),
                "end_date": now + timedelta(days=5),
                "approved_resources": "20 trained search and rescue personnel with equipment",
                "reviewed_by": users["mike.wilson"],
            },
            {
                "title": "Demo Festival - Medical Support Request",
                "description": "Medical team needed for festival coverage and emergency response.",
                "urgency": "MEDIUM",
                "requesting_org": organizations["FIRE"],
                "target_org": organizations["EMS"],
                "incident": incidents["Demo Community Festival 2025"],
                "requested_by": users["david.brown"],
                "status": "PENDING",
                "start_date": now + timedelta(days=30),
                "end_date": now + timedelta(days=32),
            },
            {
                "title": "Demo Hurricane - Emergency Shelter Support",
                "description": "Need fire department support for emergency shelter operations.",
                "urgency": "MEDIUM",
                "requesting_org": organizations["EMERGENCY_MGMT"],
                "target_org": organizations["FIRE"],
                "incident": incidents["Demo Hurricane Response 2025"],
                "requested_by": users["john.smith"],
                "status": "PENDING",
                "start_date": now + timedelta(hours=12),
                "end_date": now + timedelta(days=3),
            },
        ]

        for config in request_configs:
            support_request, created = SupportRequest.objects.get_or_create(
                title=config["title"],
                defaults={
                    "description": config["description"],
                    "urgency": config["urgency"],
                    "requesting_organization": config["requesting_org"],
                    "target_organization": config["target_org"],
                    "related_incident": config["incident"],
                    "requested_by": config["requested_by"],
                    "status": config["status"],
                    "requested_start_date": config["start_date"],
                    "requested_end_date": config["end_date"],
                    "approved_resources": config.get("approved_resources", ""),
                    "reviewed_by": config.get("reviewed_by"),
                    "reviewed_at": now if config["status"] != "PENDING" else None,
                },
            )

            if created:
                self.stdout.write(f"  ✓ Created support request: {support_request.title}")
            else:
                self.stdout.write(f"  → Support request already exists: {support_request.title}")

    def _create_checkins(self, incidents, users):
        """Create sample check-ins"""
        self.stdout.write("Creating sample check-ins...")

        # Get the active hurricane incident
        hurricane_incident = incidents["Demo Hurricane Response 2025"]

        # Create some sample check-ins with different people
        checkin_configs = [
            {
                "first_name": "Alex",
                "last_name": "Thompson",
                "roster_id": "THO001",
                "user": users.get("sarah.johnson"),  # Some may have user accounts
            },
            {
                "first_name": "Emily",
                "last_name": "Davis",
                "roster_id": "DAV002",
                "user": None,  # Some may not have user accounts
            },
            {
                "first_name": "Marcus",
                "last_name": "Williams",
                "roster_id": "WIL003",
                "user": users.get("jennifer.garcia"),
            },
            {
                "first_name": "Jessica",
                "last_name": "Lee",
                "roster_id": "LEE004",
                "user": None,
            },
        ]

        now = timezone.now()

        for i, config in enumerate(checkin_configs):
            checkin_time = now - timedelta(hours=random.randint(1, 48))

            checkin, created = CheckIn.objects.get_or_create(
                incident=hurricane_incident,
                first_name=config["first_name"],
                last_name=config["last_name"],
                roster_id=config["roster_id"],
                defaults={
                    "user": config["user"],
                    "timestamp": checkin_time,
                    "mileage": random.randint(20, 150),
                    "food_expenses": round(random.uniform(15.00, 45.00), 2),
                    "other_expenses": round(random.uniform(0.00, 25.00), 2),
                    "expense_notes": f"Demo expenses for {config['first_name']} {config['last_name']}",
                    "Check_Out": random.choice([True, False]),
                    "checkout_time": checkin_time + timedelta(hours=8)
                    if random.choice([True, False])
                    else None,
                },
            )

            if created:
                self.stdout.write(
                    f"  ✓ Created check-in for {config['first_name']} {config['last_name']}"
                )
            else:
                self.stdout.write(
                    f"  → Check-in already exists for {config['first_name']} {config['last_name']}"
                )

    def _display_summary(self):
        """Display summary of created demo data"""
        self.stdout.write(self.style.SUCCESS("\n🎉 Demo data created successfully!"))

        self.stdout.write("\n📊 Summary:")
        self.stdout.write(
            f"  Organizations: {IncidentOrganization.objects.filter(name__contains='Demo').count()}"
        )
        self.stdout.write(
            f"  Users: {User.objects.filter(username__in=['john.smith', 'sarah.johnson', 'mike.wilson', 'lisa.chen', 'david.brown', 'jennifer.garcia', 'robert.martinez', 'maria.rodriguez']).count()}"
        )
        self.stdout.write(f"  Incidents: {Incident.objects.filter(name__contains='Demo').count()}")
        self.stdout.write(
            f"  Support Requests: {SupportRequest.objects.filter(title__contains='Demo').count()}"
        )
        self.stdout.write(
            f"  Check-ins: {CheckIn.objects.filter(incident__name__contains='Demo').count()}"
        )

        self.stdout.write("\n👥 Demo Users (password: demo123):")
        self.stdout.write("  • john.smith - EMA Admin")
        self.stdout.write("  • sarah.johnson - EMA Incident Manager")
        self.stdout.write("  • mike.wilson - SDF Admin")
        self.stdout.write("  • lisa.chen - SDF Incident Manager")
        self.stdout.write("  • david.brown - Fire Dept Admin")
        self.stdout.write("  • jennifer.garcia - Fire Dept Responder")
        self.stdout.write("  • robert.martinez - Medical Center Admin")
        self.stdout.write("  • maria.rodriguez - Cross-organization user")

        # Check if superuser was added
        superuser = User.objects.filter(is_superuser=True, id=1).first()
        if superuser:
            self.stdout.write(f"  • {superuser.username} - Superuser (Owner of EMA, Member of SDF)")

        self.stdout.write("\n🚨 Active Incidents:")
        self.stdout.write("  • Demo Hurricane Response 2025 (EMA)")
        self.stdout.write("  • Demo Hurricane - SDF Support (SDF)")

        self.stdout.write("\n📋 Support Requests:")
        self.stdout.write("  • 1 Approved request (EMA → SDF)")
        self.stdout.write("  • 2 Pending requests")

        self.stdout.write("\n🌐 You can now log in and explore NetEOC!")
        self.stdout.write("   Try switching between organizations with maria.rodriguez")
