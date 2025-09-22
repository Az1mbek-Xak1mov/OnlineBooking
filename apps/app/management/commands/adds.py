from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random
from datetime import timedelta, time


from apps.authentication.models import User
from apps.app.models import ServiceCategory, Service, ServiceSchedule, Booking, WeekdayChoices, WEEKDAY_NAME_TO_INDEX



fake = Faker()


class Command(BaseCommand):
    help = "Create fake data for testing (Users, Categories, Services, Bookings...)"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=10, help="Number of users")
        parser.add_argument("--categories", type=int, default=5, help="Number of categories")
        parser.add_argument("--services", type=int, default=20, help="Number of services")
        parser.add_argument("--bookings", type=int, default=30, help="Number of bookings")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(" Generating fake data..."))

        # --- Users ---
        users = []
        for _ in range(options["users"]):
            u = User.objects.create_user(
                phone_number=fake.msisdn()[:12],
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                type=random.choice([User.Type.CUSTOMER, User.Type.PROVIDER]),
                telegram_id=random.randint(10000000, 99999999),
                password="12345",
            )
            users.append(u)
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(users)} users"))

        # --- Categories ---
        categories = []
        for _ in range(options["categories"]):
            c = ServiceCategory.objects.create(name=fake.word().capitalize())
            categories.append(c)
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(categories)} categories"))

        # --- Services + Schedules ---
        services = []
        providers = [u for u in users if u.is_provider]
        for _ in range(options["services"]):
            s = Service.objects.create(
                owner=random.choice(providers),
                category=random.choice(categories),
                name=fake.company(),
                address=fake.address(),
                capacity=random.randint(1, 20),
                duration=timedelta(minutes=random.choice([30, 60, 90, 120])),
                price=random.randint(10000, 100000),
                description=fake.text(),
            )
            services.append(s)

            # add schedules
            for day, _ in WeekdayChoices.choices:
                if random.choice([True, False]):
                    start = time(hour=random.randint(8, 18), minute=0)
                    end = (timezone.datetime.combine(timezone.now(), start) + timedelta(hours=2)).time()
                    ServiceSchedule.objects.create(
                        service=s, weekday=day, start_time=start, end_time=end
                    )

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(services)} services with schedules"))

        # --- Bookings ---
        bookings = []
        customers = [u for u in users if u.is_customer]
        for _ in range(options["bookings"]):
            service = random.choice(services)
            user = random.choice(customers)
            weekday = random.choice(list(WEEKDAY_NAME_TO_INDEX.keys()))
            date = timezone.localdate() + timedelta(days=random.randint(0, 14))
            start_time = time(hour=random.randint(9, 17), minute=0)
            end_time = (timezone.datetime.combine(timezone.now(), start_time) + timedelta(hours=1)).time()
            b = Booking.objects.create(
                service=service,
                weekday=weekday,
                user=user,
                date=date,
                start_time=start_time,
                end_time=end_time,
                seats=random.randint(1, min(5, service.capacity)),
            )
            bookings.append(b)

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(bookings)} bookings"))

        self.stdout.write(self.style.SUCCESS(" Fake data successfully generated!"))
