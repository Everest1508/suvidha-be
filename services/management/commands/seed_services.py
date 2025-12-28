from django.core.management.base import BaseCommand
from services.models import ServiceCategory


class Command(BaseCommand):
    help = 'Seed initial service categories'

    def handle(self, *args, **options):
        services = [
            {'name': 'AC', 'slug': 'ac', 'icon': 'ac'},
            {'name': 'Cleaning', 'slug': 'cleaning', 'icon': 'cleaning'},
            {'name': 'Plumber', 'slug': 'plumber', 'icon': 'plumber'},
            {'name': 'Electrician', 'slug': 'electrician', 'icon': 'electrician'},
            {'name': 'Carpenter', 'slug': 'carpenter', 'icon': 'carpenter'},
            {'name': 'Car-Wash', 'slug': 'car-wash', 'icon': 'car-wash'},
            {'name': 'Painter', 'slug': 'painter', 'icon': 'painter'},
            {'name': 'TV Repair', 'slug': 'tv-repair', 'icon': 'tv-repair'},
            {'name': 'Security', 'slug': 'security', 'icon': 'security'},
        ]
        
        created_count = 0
        for service_data in services:
            service, created = ServiceCategory.objects.get_or_create(
                slug=service_data['slug'],
                defaults=service_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created service: {service.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Service already exists: {service.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} new service categories.')
        )

