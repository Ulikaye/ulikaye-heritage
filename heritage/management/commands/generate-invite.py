from django.core.management.base import BaseCommand
from heritage.models import InviteCode
import random
import string

class Command(BaseCommand):
    help = 'Generate invitation codes'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Number of codes to generate')

    def handle(self, *args, **options):
        count = options['count']
        for _ in range(count):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            InviteCode.objects.create(code=code)
            self.stdout.write(f"Generated: {code}")