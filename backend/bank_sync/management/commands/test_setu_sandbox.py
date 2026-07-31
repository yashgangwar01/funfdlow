from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from bank_sync.models import ConsentRequest
from bank_sync.setu_client import SetuAAClient, SetuAPIError

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a test consent request via Setu AA Client and prints the sandbox redirect URL.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vua',
            default='9999999999@onemoney',
            help='Virtual User Address for the sandbox test, e.g. 9999999999@onemoney (default: 9999999999@onemoney)'
        )

    def handle(self, *args, **options):
        vua = options['vua']
        self.stdout.write("Initializing Setu AA Sandbox Consent Request...")

        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found in database. Run seed_demo_data first."))
            return

        client = SetuAAClient()
        self.stdout.write(f"Connecting to Setu Sandbox URL: {client.base_url}")
        self.stdout.write(f"Target User: {user.email}")
        self.stdout.write(f"VUA: {vua}")

        try:
            res = client.create_consent_request(user, vua=vua)
        except SetuAPIError as e:
            self.stdout.write(self.style.ERROR(f"\nSetu API request failed: {e}"))
            raise SystemExit(1)

        handle = res.get('consent_handle')
        redirect_url = res.get('redirect_url')

        ConsentRequest.objects.create(
            user=user,
            consent_handle=handle,
            status='PENDING',
            redirect_url=redirect_url
        )

        self.stdout.write(self.style.SUCCESS("\nSetu Sandbox Consent Created Successfully!"))
        self.stdout.write(f"Consent Handle: {handle}")
        self.stdout.write(self.style.WARNING(f"\nLaunch Pre-built Consent Screen in Browser:\n{redirect_url}\n"))
