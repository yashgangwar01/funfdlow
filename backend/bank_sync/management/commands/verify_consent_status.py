"""
Management command: verify_consent_status

Usage:
  .\venv\Scripts\python.exe manage.py verify_consent_status <consent_handle>

Checks Setu's real record of a consent and prints the full status.
"""
import json
from django.core.management.base import BaseCommand
from bank_sync.models import ConsentRequest
from bank_sync.setu_client import SetuAAClient, SetuAPIError
import requests


class Command(BaseCommand):
    help = 'Checks Setu sandbox for the real status of a consent handle.'

    def add_arguments(self, parser):
        parser.add_argument(
            'consent_handle',
            nargs='?',
            default=None,
            help='The Setu consent handle UUID. If omitted, uses the most recent one in the DB.'
        )

    def handle(self, *args, **options):
        handle = options['consent_handle']

        if not handle:
            latest = ConsentRequest.objects.order_by('-created_at').first()
            if not latest:
                self.stdout.write(self.style.ERROR("No ConsentRequest rows found in DB."))
                return
            handle = latest.consent_handle
            self.stdout.write(f"No handle provided — using most recent: {handle}")

        # Show DB record
        db_record = ConsentRequest.objects.filter(consent_handle=handle).first()
        if db_record:
            self.stdout.write(f"\n--- DB Record ---")
            self.stdout.write(f"  consent_handle : {db_record.consent_handle}")
            self.stdout.write(f"  status (DB)    : {db_record.status}")
            self.stdout.write(f"  user           : {db_record.user}")
            self.stdout.write(f"  created_at     : {db_record.created_at}")
        else:
            self.stdout.write(self.style.WARNING(f"No DB record found for handle: {handle}"))

        # Check Setu's real record
        client = SetuAAClient()
        token = client._get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'x-product-instance-id': client.product_instance_id,
            'Content-Type': 'application/json',
        }

        url = f"{client.base_url}/v2/consents/{handle}"
        self.stdout.write(f"\n--- Setu API: GET {url} ---")

        try:
            res = requests.get(url, headers=headers, timeout=15)
            self.stdout.write(f"HTTP Status: {res.status_code}")
            data = res.json()
            self.stdout.write(json.dumps(data, indent=2))

            setu_status = (
                data.get('status') or
                (data.get('detail') or {}).get('status') or
                'UNKNOWN'
            )
            accounts_linked = data.get('accountsLinked', [])

            self.stdout.write(f"\n>>> Setu status        : {setu_status}")
            self.stdout.write(f">>> accountsLinked     : {len(accounts_linked)} account(s)")

            if setu_status.upper() in ('ACTIVE', 'APPROVED'):
                self.stdout.write(self.style.SUCCESS("Consent is APPROVED on Setu's side."))
                if db_record and db_record.status != 'APPROVED':
                    db_record.status = 'APPROVED'
                    db_record.save()
                    self.stdout.write(self.style.SUCCESS("DB status updated to APPROVED."))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Consent is still '{setu_status}' on Setu's side. "
                    "The browser consent flow was not completed."
                ))

        except SetuAPIError as e:
            self.stdout.write(self.style.ERROR(f"SetuAPIError: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
