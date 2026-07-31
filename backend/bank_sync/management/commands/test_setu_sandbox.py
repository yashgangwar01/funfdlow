from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from bank_sync.models import ConsentRequest
from bank_sync.setu_client import SetuAAClient

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a test consent request via Setu AA Client and prints the sandbox redirect URL.'

    def handle(self, *args, **options):
        self.stdout.write("Initializing Setu AA Sandbox Consent Request...")

        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found in database. Run seed_demo_data first."))
            return

        client = SetuAAClient()
        self.stdout.write(f"Connecting to Setu Sandbox URL: {client.base_url}")
        self.stdout.write(f"Target User: {user.email}")

        res = client.create_consent_request(user)
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
