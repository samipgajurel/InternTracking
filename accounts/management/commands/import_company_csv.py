import csv
import secrets
import string

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from internships.models import SupervisorIntern


def make_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Import company interns CSV, create supervisor, create interns, assign them to supervisor."

    def add_arguments(self, parser):
        parser.add_argument("--csv", required=True, help="Absolute path to CSV file")
        parser.add_argument("--company", required=True, help="Company code, e.g., CTPL")
        parser.add_argument("--supervisor_email", required=True)
        parser.add_argument("--supervisor_name", required=True)
        parser.add_argument("--supervisor_idcard", required=True)
        parser.add_argument("--verify", action="store_true", help="Mark created users as verified")
        parser.add_argument(
            "--password_mode",
            choices=["random", "idcard", "unusable"],
            default="random",
            help="Password strategy for created interns",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        csv_path = opts["csv"]
        company = (opts["company"] or "").strip()
        sup_email = (opts["supervisor_email"] or "").strip().lower()
        sup_name = (opts["supervisor_name"] or "").strip()
        sup_idcard = (opts["supervisor_idcard"] or "").strip()
        verify = bool(opts["verify"])
        password_mode = opts["password_mode"]

        # 1) Create / update supervisor
        supervisor, created = User.objects.get_or_create(
            email=sup_email,
            defaults={
                "full_name": sup_name,
                "role": "supervisor",
                "company_code": company,
                "id_card_no": sup_idcard,
                "is_verified": verify,
            },
        )
        if not created:
            supervisor.full_name = sup_name or supervisor.full_name
            supervisor.role = "supervisor"
            supervisor.company_code = company
            supervisor.id_card_no = sup_idcard
            if verify:
                supervisor.is_verified = True
            supervisor.save()

        self.stdout.write(self.style.SUCCESS(f"Supervisor OK: {supervisor.email} ({supervisor.staff_id})"))

        # 2) Import interns
        created_interns = 0
        updated_interns = 0

        # Optional: print passwords so admin can share
        credentials_out = []

        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            # Expected columns from your CSV:
            # Intern Name, E-mail, ID Info, Role ...
            for row in reader:
                name = (row.get("Intern Name") or "").strip()
                email = (row.get("E-mail") or "").strip().lower()
                id_card = (row.get("ID Info") or "").strip()

                if not email or not name:
                    continue

                intern = User.objects.filter(email=email).first()
                is_new = intern is None

                if is_new:
                    if password_mode == "unusable":
                        pwd = None
                    elif password_mode == "idcard" and id_card:
                        pwd = id_card  # not recommended, but supported
                    else:
                        pwd = make_password()

                    intern = User.objects.create_user(
                        email=email,
                        full_name=name,
                        password=pwd,
                        role="intern",
                        company_code=company,
                        id_card_no=id_card,
                        is_verified=verify,
                    )
                    created_interns += 1

                    credentials_out.append({
                        "email": email,
                        "full_name": name,
                        "password": pwd if pwd else "(unusable - use forgot password)",
                        "staff_id": intern.staff_id,
                        "id_card_no": id_card,
                    })
                else:
                    intern.full_name = name or intern.full_name
                    intern.role = "intern"
                    intern.company_code = company
                    intern.id_card_no = id_card or intern.id_card_no
                    if verify:
                        intern.is_verified = True
                    intern.save()
                    updated_interns += 1

                # 3) Assign intern -> supervisor
                SupervisorIntern.objects.update_or_create(
                    intern=intern,
                    defaults={"supervisor": supervisor},
                )

        self.stdout.write(self.style.SUCCESS(f"Interns created: {created_interns}, updated: {updated_interns}"))
        self.stdout.write(self.style.SUCCESS("Assignments: ALL interns assigned to supervisor."))

        # Print generated credentials
        if credentials_out:
            self.stdout.write("\n=== GENERATED CREDENTIALS (save this) ===")
            for c in credentials_out:
                self.stdout.write(f'{c["email"]} | {c["password"]} | {c["staff_id"]} | {c["id_card_no"]}')
