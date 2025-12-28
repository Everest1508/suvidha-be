from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from providers.models import ServiceProvider, ProviderService
from services.models import ServiceCategory
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed sample service providers with different services'

    def handle(self, *args, **options):
        # Get service categories
        services = {
            'ac': ServiceCategory.objects.filter(slug='ac').first(),
            'cleaning': ServiceCategory.objects.filter(slug='cleaning').first(),
            'plumber': ServiceCategory.objects.filter(slug='plumber').first(),
            'electrician': ServiceCategory.objects.filter(slug='electrician').first(),
            'carpenter': ServiceCategory.objects.filter(slug='carpenter').first(),
            'car-wash': ServiceCategory.objects.filter(slug='car-wash').first(),
            'painter': ServiceCategory.objects.filter(slug='painter').first(),
            'tv-repair': ServiceCategory.objects.filter(slug='tv-repair').first(),
            'security': ServiceCategory.objects.filter(slug='security').first(),
        }

        # Sample providers data - Nashik area coordinates
        providers_data = [
            {
                'username': 'rajesh_plumber',
                'email': 'rajesh.plumber@example.com',
                'password': 'Test@123',
                'phone': '9876543210',
                'name': 'Rajesh Kumar - Expert Plumber',
                'contact': '9876543210',
                'address': 'Near City Center, Nashik',
                'latitude': Decimal('19.9975'),
                'longitude': Decimal('73.7898'),
                'location_string': 'City Center, Nashik, Maharashtra',
                'services': ['plumber'],
            },
            {
                'username': 'priya_electrician',
                'email': 'priya.electrician@example.com',
                'password': 'Test@123',
                'phone': '9876543211',
                'name': 'Priya Electrical Services',
                'contact': '9876543211',
                'address': 'Gangapur Road, Nashik',
                'latitude': Decimal('19.9950'),
                'longitude': Decimal('73.7920'),
                'location_string': 'Gangapur Road, Nashik, Maharashtra',
                'services': ['electrician'],
            },
            {
                'username': 'amit_carpenter',
                'email': 'amit.carpenter@example.com',
                'password': 'Test@123',
                'phone': '9876543212',
                'name': 'Amit Wood Works',
                'contact': '9876543212',
                'address': 'Satpur Industrial Area, Nashik',
                'latitude': Decimal('19.9900'),
                'longitude': Decimal('73.7800'),
                'location_string': 'Satpur, Nashik, Maharashtra',
                'services': ['carpenter'],
            },
            {
                'username': 'sneha_cleaning',
                'email': 'sneha.cleaning@example.com',
                'password': 'Test@123',
                'phone': '9876543213',
                'name': 'Sneha Home Cleaning Services',
                'contact': '9876543213',
                'address': 'College Road, Nashik',
                'latitude': Decimal('19.9980'),
                'longitude': Decimal('73.7910'),
                'location_string': 'College Road, Nashik, Maharashtra',
                'services': ['cleaning'],
            },
            {
                'username': 'vijay_painter',
                'email': 'vijay.painter@example.com',
                'password': 'Test@123',
                'phone': '9876543214',
                'name': 'Vijay Paint & Decor',
                'contact': '9876543214',
                'address': 'Nashik Road, Nashik',
                'latitude': Decimal('19.9850'),
                'longitude': Decimal('73.7950'),
                'location_string': 'Nashik Road, Nashik, Maharashtra',
                'services': ['painter'],
            },
            {
                'username': 'rohan_carwash',
                'email': 'rohan.carwash@example.com',
                'password': 'Test@123',
                'phone': '9876543215',
                'name': 'Rohan Auto Care',
                'contact': '9876543215',
                'address': 'Dwarka Circle, Nashik',
                'latitude': Decimal('19.9920'),
                'longitude': Decimal('73.7880'),
                'location_string': 'Dwarka Circle, Nashik, Maharashtra',
                'services': ['car-wash'],
            },
            {
                'username': 'anita_ac',
                'email': 'anita.ac@example.com',
                'password': 'Test@123',
                'phone': '9876543216',
                'name': 'Anita AC Services',
                'contact': '9876543216',
                'address': 'Panchavati, Nashik',
                'latitude': Decimal('19.9990'),
                'longitude': Decimal('73.7900'),
                'location_string': 'Panchavati, Nashik, Maharashtra',
                'services': ['ac'],
            },
            {
                'username': 'mahesh_tvrepair',
                'email': 'mahesh.tvrepair@example.com',
                'password': 'Test@123',
                'phone': '9876543217',
                'name': 'Mahesh Electronics Repair',
                'contact': '9876543217',
                'address': 'Old Nashik, Nashik',
                'latitude': Decimal('19.9930'),
                'longitude': Decimal('73.7870'),
                'location_string': 'Old Nashik, Nashik, Maharashtra',
                'services': ['tv-repair'],
            },
            {
                'username': 'security_services',
                'email': 'security.services@example.com',
                'password': 'Test@123',
                'phone': '9876543218',
                'name': 'Nashik Security Solutions',
                'contact': '9876543218',
                'address': 'CIDCO, Nashik',
                'latitude': Decimal('19.9670'),
                'longitude': Decimal('73.7540'),
                'location_string': 'CIDCO, Nashik, Maharashtra',
                'services': ['security'],
            },
            {
                'username': 'multi_service',
                'email': 'multi.service@example.com',
                'password': 'Test@123',
                'phone': '9876543219',
                'name': 'Multi Service Provider',
                'contact': '9876543219',
                'address': 'Mahatma Nagar, Nashik',
                'latitude': Decimal('19.9955'),
                'longitude': Decimal('73.7895'),
                'location_string': 'Mahatma Nagar, Nashik, Maharashtra',
                'services': ['plumber', 'electrician', 'carpenter'],
            },
        ]

        created_count = 0
        for provider_data in providers_data:
            # Check if user already exists
            username = provider_data['username']
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'Provider already exists: {provider_data["name"]}')
                )
                continue

            # Create user
            user = User.objects.create_user(
                username=provider_data['username'],
                email=provider_data['email'],
                password=provider_data['password'],
                phone=provider_data['phone'],
                role='provider'
            )

            # Create service provider
            provider = ServiceProvider.objects.create(
                user=user,
                name=provider_data['name'],
                contact=provider_data['contact'],
                address=provider_data['address'],
                latitude=provider_data['latitude'],
                longitude=provider_data['longitude'],
                location_string=provider_data['location_string'],
                verification_status='approved',  # Auto-approve for seed data
                onboarding_step=3,
                is_onboarding_complete=True
            )

            # Add services
            for service_slug in provider_data['services']:
                service_category = services.get(service_slug)
                if service_category:
                    ProviderService.objects.get_or_create(
                        provider=provider,
                        service_category=service_category
                    )

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created provider: {provider_data["name"]} with services: {", ".join(provider_data["services"])}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} service providers.')
        )

