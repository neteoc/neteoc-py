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
    AssetCategory,
    Asset,
)


class Command(BaseCommand):
    help = "Create sample data for NetEOC demonstration"

    # Constants to avoid string duplication
    USERNAME_JOHN_SMITH = "john.smith"
    USERNAME_SARAH_JOHNSON = "sarah.johnson"
    USERNAME_MIKE_WILSON = "mike.wilson"
    USERNAME_LISA_CHEN = "lisa.chen"
    USERNAME_DAVID_BROWN = "david.brown"
    USERNAME_JENNIFER_GARCIA = "jennifer.garcia"
    USERNAME_ROBERT_MARTINEZ = "robert.martinez"
    USERNAME_MARIA_RODRIGUEZ = "maria.rodriguez"

    INCIDENT_HURRICANE_2025 = "Demo Hurricane Response 2025"
    CATEGORY_MEDICAL_EQUIPMENT = "Medical Equipment"

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

        # Create sample asset categories and assets
        self._create_asset_categories()
        self._create_assets(organizations)

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

        # Clear assets (demo assets have specific identifiers)
        Asset.objects.filter(identifier__startswith="EMA-").delete()
        Asset.objects.filter(identifier__startswith="SDF-").delete()
        Asset.objects.filter(identifier__startswith="FD-").delete()
        Asset.objects.filter(identifier__startswith="MED-").delete()

        # Clear asset categories
        AssetCategory.objects.all().delete()

        Incident.objects.filter(name__contains="Demo").delete()

        # Delete demo users (but keep admin users)
        demo_users = User.objects.filter(
            username__in=[
                self.USERNAME_JOHN_SMITH,
                self.USERNAME_SARAH_JOHNSON,
                self.USERNAME_MIKE_WILSON,
                self.USERNAME_LISA_CHEN,
                self.USERNAME_DAVID_BROWN,
                self.USERNAME_JENNIFER_GARCIA,
                self.USERNAME_ROBERT_MARTINEZ,
                self.USERNAME_MARIA_RODRIGUEZ,
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
                "username": self.USERNAME_JOHN_SMITH,
                "email": "john.smith@democounty.gov",
                "first_name": "John",
                "last_name": "Smith",
                "organizations": ["EMERGENCY_MGMT"],
                "roles": ["ADMIN"],
            },
            {
                "username": self.USERNAME_SARAH_JOHNSON,
                "email": "sarah.johnson@democounty.gov",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "organizations": ["EMERGENCY_MGMT"],
                "roles": ["INCIDENT_MANAGER"],
            },
            {
                "username": self.USERNAME_MIKE_WILSON,
                "email": "mike.wilson@demosdf.mil",
                "first_name": "Mike",
                "last_name": "Wilson",
                "organizations": ["STATE"],
                "roles": ["ADMIN"],
            },
            {
                "username": self.USERNAME_LISA_CHEN,
                "email": "lisa.chen@demosdf.mil",
                "first_name": "Lisa",
                "last_name": "Chen",
                "organizations": ["STATE"],
                "roles": ["INCIDENT_MANAGER"],
            },
            {
                "username": self.USERNAME_DAVID_BROWN,
                "email": "david.brown@democityfd.org",
                "first_name": "David",
                "last_name": "Brown",
                "organizations": ["FIRE"],
                "roles": ["ADMIN"],
            },
            {
                "username": self.USERNAME_JENNIFER_GARCIA,
                "email": "jennifer.garcia@democityfd.org",
                "first_name": "Jennifer",
                "last_name": "Garcia",
                "organizations": ["FIRE"],
                "roles": ["RESPONDER"],
            },
            {
                "username": self.USERNAME_ROBERT_MARTINEZ,
                "email": "robert.martinez@demomedical.org",
                "first_name": "Robert",
                "last_name": "Martinez",
                "organizations": ["EMS"],
                "roles": ["ADMIN"],
            },
            {
                "username": self.USERNAME_MARIA_RODRIGUEZ,
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

                _, created = IncidentOrganizationUser.objects.get_or_create(
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
            _, created = IncidentOrganizationUser.objects.get_or_create(
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
                "name": self.INCIDENT_HURRICANE_2025,
                "type": "HURRICANE",
                "description": "Category 3 hurricane making landfall in Demo County. Coordinated multi-agency response required.",
                "status": "ACTIVE",
                "organization": organizations["EMERGENCY_MGMT"],
                "owner": users[self.USERNAME_JOHN_SMITH],
                "commander": users[self.USERNAME_SARAH_JOHNSON],
                "start_date": now - timedelta(days=2),
                "location": "Demo County, Florida",
            },
            {
                "name": "Demo Hurricane - SDF Support",
                "type": "HURRICANE",
                "description": "State Defense Force support mission for Demo County hurricane response.",
                "status": "ACTIVE",
                "organization": organizations["STATE"],
                "owner": users[self.USERNAME_MIKE_WILSON],
                "commander": users[self.USERNAME_LISA_CHEN],
                "start_date": now - timedelta(days=1),
                "location": "Demo County, Florida",
            },
            {
                "name": "Demo Community Festival 2025",
                "type": "FESTIVAL",
                "description": "Annual Demo City Summer Festival - medical and safety support required.",
                "status": "STANDBY",
                "organization": organizations["FIRE"],
                "owner": users[self.USERNAME_DAVID_BROWN],
                "commander": users[self.USERNAME_JENNIFER_GARCIA],
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
                "owner": users[self.USERNAME_JOHN_SMITH],
                "commander": users[self.USERNAME_SARAH_JOHNSON],
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

    def _create_asset_categories(self):
        """Create sample asset categories"""
        self.stdout.write("Creating sample asset categories...")

        category_configs = [
            {
                "name": "Radios",
                "description": "Two-way radios and communication equipment",
                "requires_license": True,
                "requires_training": True,
            },
            {
                "name": "Vehicles",
                "description": "Emergency response vehicles and transportation",
                "requires_license": True,
                "requires_training": False,
            },
            {
                "name": "Laptops",
                "description": "Portable computers and tablets for field operations",
                "requires_license": False,
                "requires_training": False,
            },
            {
                "name": self.CATEGORY_MEDICAL_EQUIPMENT,
                "description": "Medical devices and emergency medical supplies",
                "requires_license": False,
                "requires_training": True,
            },
            {
                "name": "Generators",
                "description": "Portable power generators for emergency operations",
                "requires_license": False,
                "requires_training": True,
            },
        ]

        categories = {}
        for config in category_configs:
            category, created = AssetCategory.objects.get_or_create(
                name=config["name"],
                defaults={
                    "description": config["description"],
                    "requires_license": config["requires_license"],
                    "requires_training": config["requires_training"],
                },
            )
            categories[config["name"]] = category

            if created:
                self.stdout.write(f"  ✓ Created asset category: {category.name}")
            else:
                self.stdout.write(f"  → Asset category already exists: {category.name}")

        return categories

    def _create_assets(self, organizations):
        """Create sample assets"""
        self.stdout.write("Creating sample assets...")

        # Get asset categories
        categories = {
            "Radios": AssetCategory.objects.get(name="Radios"),
            "Vehicles": AssetCategory.objects.get(name="Vehicles"),
            "Laptops": AssetCategory.objects.get(name="Laptops"),
            self.CATEGORY_MEDICAL_EQUIPMENT: AssetCategory.objects.get(
                name=self.CATEGORY_MEDICAL_EQUIPMENT
            ),
            "Generators": AssetCategory.objects.get(name="Generators"),
        }

        asset_configs = [
            # EMA Assets
            {
                "identifier": "EMA-RADIO-001",
                "name": "Motorola XPR 7550e",
                "description": "Digital two-way radio for emergency communications",
                "category": categories["Radios"],
                "organization": organizations["EMERGENCY_MGMT"],
                "frequency": "155.175 MHz",
                "call_sign": "KC1ABC",
                "value": 450.00,
            },
            {
                "identifier": "EMA-RADIO-002",
                "name": "Motorola XPR 7550e",
                "description": "Digital two-way radio for emergency communications",
                "category": categories["Radios"],
                "organization": organizations["EMERGENCY_MGMT"],
                "frequency": "155.175 MHz",
                "call_sign": "KC1ABD",
                "value": 450.00,
            },
            {
                "identifier": "EMA-VEH-001",
                "name": "Ford F-150 Command Vehicle",
                "description": "Mobile command vehicle for incident management",
                "category": categories["Vehicles"],
                "organization": organizations["EMERGENCY_MGMT"],
                "license_plate": "EMA001",
                "vin": "1FTFW1ET5DKF12345",
                "fuel_type": "Gasoline",
                "value": 45000.00,
            },
            {
                "identifier": "EMA-LAP-001",
                "name": "Dell Latitude 5520",
                "description": "Rugged laptop for field operations",
                "category": categories["Laptops"],
                "organization": organizations["EMERGENCY_MGMT"],
                "serial_number": "DLAT5520001",
                "value": 1200.00,
            },
            {
                "identifier": "EMA-GEN-001",
                "name": "Honda EU7000iS Generator",
                "description": "Portable inverter generator for emergency power",
                "category": categories["Generators"],
                "organization": organizations["EMERGENCY_MGMT"],
                "serial_number": "EUGX-1234567",
                "fuel_type": "Gasoline",
                "value": 4500.00,
            },
            # SDF Assets
            {
                "identifier": "SDF-RADIO-001",
                "name": "Harris XL-200P",
                "description": "Military-grade portable radio",
                "category": categories["Radios"],
                "organization": organizations["STATE"],
                "frequency": "406.125 MHz",
                "call_sign": "KA1XYZ",
                "value": 800.00,
            },
            {
                "identifier": "SDF-VEH-001",
                "name": "Chevrolet Tahoe",
                "description": "Command and control vehicle",
                "category": categories["Vehicles"],
                "organization": organizations["STATE"],
                "license_plate": "SDF001",
                "vin": "1GNSKCKC5HR123456",
                "fuel_type": "Gasoline",
                "value": 55000.00,
            },
            {
                "identifier": "SDF-LAP-001",
                "name": "Panasonic Toughbook CF-33",
                "description": "Fully rugged 2-in-1 detachable laptop",
                "category": categories["Laptops"],
                "organization": organizations["STATE"],
                "serial_number": "CF33001234",
                "value": 3500.00,
            },
            # Fire Department Assets
            {
                "identifier": "FD-RADIO-001",
                "name": "Motorola APX 6000",
                "description": "Fire department tactical radio",
                "category": categories["Radios"],
                "organization": organizations["FIRE"],
                "frequency": "154.265 MHz",
                "call_sign": "KD1FIR",
                "value": 650.00,
            },
            {
                "identifier": "FD-VEH-001",
                "name": "Pierce Fire Engine",
                "description": "Class A fire engine with 1500 GPM pump",
                "category": categories["Vehicles"],
                "organization": organizations["FIRE"],
                "license_plate": "FD-E01",
                "fuel_type": "Diesel",
                "value": 750000.00,
            },
            # Medical Center Assets
            {
                "identifier": "MED-RADIO-001",
                "name": "Kenwood NX-5200",
                "description": "Digital radio for medical communications",
                "category": categories["Radios"],
                "organization": organizations["EMS"],
                "frequency": "155.340 MHz",
                "call_sign": "KC1MED",
                "value": 400.00,
            },
            {
                "identifier": "MED-LAP-001",
                "name": "HP EliteBook 840",
                "description": "Medical records and communication laptop",
                "category": categories["Laptops"],
                "organization": organizations["EMS"],
                "serial_number": "HP840001234",
                "value": 1100.00,
            },
            {
                "identifier": "MED-EQUIP-001",
                "name": "Zoll X-Series Monitor",
                "description": "Advanced life support monitor/defibrillator",
                "category": categories[self.CATEGORY_MEDICAL_EQUIPMENT],
                "organization": organizations["EMS"],
                "serial_number": "ZOLL12345678",
                "value": 25000.00,
            },
        ]

        assets = {}
        for config in asset_configs:
            asset, created = Asset.objects.get_or_create(
                identifier=config["identifier"],
                organization=config["organization"],
                defaults={
                    "name": config["name"],
                    "description": config["description"],
                    "category": config["category"],
                    "status": "AVAILABLE",
                    "serial_number": config.get("serial_number", ""),
                    "value": config.get("value"),
                    "frequency": config.get("frequency", ""),
                    "call_sign": config.get("call_sign", ""),
                    "license_plate": config.get("license_plate", ""),
                    "vin": config.get("vin", ""),
                    "fuel_type": config.get("fuel_type", ""),
                },
            )
            assets[config["identifier"]] = asset

            if created:
                self.stdout.write(f"  ✓ Created asset: {asset.identifier} - {asset.name}")
            else:
                self.stdout.write(f"  → Asset already exists: {asset.identifier}")

        return assets

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
                "incident": incidents[self.INCIDENT_HURRICANE_2025],
                "requested_by": users[self.USERNAME_SARAH_JOHNSON],
                "status": "APPROVED",
                "start_date": now + timedelta(hours=6),
                "end_date": now + timedelta(days=5),
                "approved_resources": "20 trained search and rescue personnel with equipment",
                "reviewed_by": users[self.USERNAME_MIKE_WILSON],
            },
            {
                "title": "Demo Festival - Medical Support Request",
                "description": "Medical team needed for festival coverage and emergency response.",
                "urgency": "MEDIUM",
                "requesting_org": organizations["FIRE"],
                "target_org": organizations["EMS"],
                "incident": incidents["Demo Community Festival 2025"],
                "requested_by": users[self.USERNAME_DAVID_BROWN],
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
                "incident": incidents[self.INCIDENT_HURRICANE_2025],
                "requested_by": users[self.USERNAME_JOHN_SMITH],
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
        hurricane_incident = incidents[self.INCIDENT_HURRICANE_2025]

        # Create some sample check-ins with different people
        checkin_configs = [
            {
                "first_name": "Alex",
                "last_name": "Thompson",
                "roster_id": "THO001",
                "user": users.get(self.USERNAME_SARAH_JOHNSON),  # Some may have user accounts
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
                "user": users.get(self.USERNAME_JENNIFER_GARCIA),
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

            _, created = CheckIn.objects.get_or_create(
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
            f"  Users: {User.objects.filter(username__in=[self.USERNAME_JOHN_SMITH, self.USERNAME_SARAH_JOHNSON, self.USERNAME_MIKE_WILSON, self.USERNAME_LISA_CHEN, self.USERNAME_DAVID_BROWN, self.USERNAME_JENNIFER_GARCIA, self.USERNAME_ROBERT_MARTINEZ, self.USERNAME_MARIA_RODRIGUEZ]).count()}"
        )
        self.stdout.write(f"  Incidents: {Incident.objects.filter(name__contains='Demo').count()}")
        self.stdout.write(
            f"  Support Requests: {SupportRequest.objects.filter(title__contains='Demo').count()}"
        )
        self.stdout.write(
            f"  Check-ins: {CheckIn.objects.filter(incident__name__contains='Demo').count()}"
        )
        self.stdout.write(f"  Asset Categories: {AssetCategory.objects.count()}")
        self.stdout.write(f"  Assets: {Asset.objects.count()}")

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

        self.stdout.write("\n📦 Asset Categories:")
        self.stdout.write("  • Radios (5 assets)")
        self.stdout.write("  • Vehicles (3 assets)")
        self.stdout.write("  • Laptops (4 assets)")
        self.stdout.write("  • Medical Equipment (1 asset)")
        self.stdout.write("  • Generators (1 asset)")

        self.stdout.write("\n🌐 You can now log in and explore NetEOC!")
        self.stdout.write("   Try the new Asset Management system at /operations/assets/")
        self.stdout.write("   Try switching between organizations with maria.rodriguez")
