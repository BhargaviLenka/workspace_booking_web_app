from django.core.management.base import BaseCommand
from booking.services.redis_setup import create_or_update_weekly_availability

class Command(BaseCommand):
    help = "Initialize or refresh Redis availability keys for upcoming week"

    def handle(self, *args, **options):
        create_or_update_weekly_availability()
        self.stdout.write(self.style.SUCCESS("Redis availability initialized for the upcoming week."))