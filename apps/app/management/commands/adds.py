import random
from datetime import time, timedelta

from app.models import (WEEKDAY_NAME_TO_INDEX, Booking, Service,
                        ServiceCategory, ServiceSchedule, WeekdayChoices)
from authentication.models import RoleChange, User
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker


class Command(BaseCommand):
    help = "Bu komanda malumot qoshish uchun"
    model_list = {"users", "categories", "services", "bookings", "rolechanges"}

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int)
        parser.add_argument("--categories", type=int)
        parser.add_argument("--services", type=int)
        parser.add_argument("--bookings", type=int)
        parser.add_argument("--rolechanges", type=int)
        parser.add_argument("--all", action="store_true")

    def _generate_users(self, number: int = 10):
        users = []
        for _ in range(number):
            while True:
                phone_number = "998" + "".join([str(random.randint(0, 9)) for _ in range(9)])
                if not User.objects.filter(phone_number=phone_number).exists():
                    break

            u = User.objects.create_user(
                phone_number=phone_number,
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                type=random.choice([User.Type.CUSTOMER, User.Type.PROVIDER]),
                telegram_id=random.randint(10000000, 99999999),
                password="1",
            )
            users.append(u)

        self.stdout.write(self.style.SUCCESS(f"Users generated - {len(users)}"))

    def _generate_categories(self, number: int = 5):
        categories = []
        for _ in range(number):
            c = ServiceCategory.objects.create(name=self.faker.word().capitalize())
            categories.append(c)
        self.stdout.write(self.style.SUCCESS(f"Categories generated - {len(categories)}"))

    def _generate_services(self, number: int = 20):
        providers = list(User.objects.filter(type=User.Type.PROVIDER))
        categories = list(ServiceCategory.objects.all())

        if not providers or not categories:
            self.stdout.write(self.style.ERROR("No providers or categories"))
            return

        services = []
        for _ in range(number):
            s = Service.objects.create(
                owner=random.choice(providers),
                category=random.choice(categories),
                name=self.faker.company(),
                address=self.faker.address(),
                capacity=random.randint(1, 20),
                duration=timedelta(minutes=random.choice([30, 60, 90, 120])),
                price=random.randint(10000, 100000),
                description=self.faker.text(),
            )
            services.append(s)

            # schedules
            for day, _ in WeekdayChoices.choices:
                if random.choice([True, False]):
                    start = time(hour=random.randint(8, 18), minute=0)
                    end = (timezone.datetime.combine(timezone.now(), start) + timedelta(hours=2)).time()
                    ServiceSchedule.objects.create(
                        service=s,
                        weekday=day,
                        start_time=start,
                        end_time=end,
                    )

        self.stdout.write(self.style.SUCCESS(f"Services generated - {len(services)}"))

    def _generate_bookings(self, number: int = 30):
        customers = list(User.objects.filter(type=User.Type.CUSTOMER))
        services = list(Service.objects.all())

        if not customers or not services:
            self.stdout.write(self.style.ERROR("No customers or services"))
            return

        bookings = []
        for _ in range(number):
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

        self.stdout.write(self.style.SUCCESS(f"Bookings generated - {len(bookings)}"))

    def _generate_rolechanges(self, number: int = 10):  # 🔹 новый генератор
        customers = list(User.objects.filter(type=User.Type.CUSTOMER))
        if not customers:
            self.stdout.write(self.style.ERROR("No customers for role change requests"))
            return

        role_changes = []
        for _ in range(number):
            user = random.choice(customers)
            is_read = random.choice([True, False])
            is_accepted = random.choice([True, False]) if is_read else None

            rc = RoleChange.objects.create(
                user=user,
                message=self.faker.sentence(),
                is_read=is_read,
                is_accepted=is_accepted,
            )
            role_changes.append(rc)

        self.stdout.write(self.style.SUCCESS(f"RoleChange requests generated - {len(role_changes)}"))

    def handle(self, *args, **kwargs):
        self.faker = Faker("uz_UZ")

        if kwargs.get("all"):
            order = ["categories", "users", "services", "bookings", "rolechanges"]
            for _name in order:
                getattr(self, f"_generate_{_name}")()
        else:
            specified = {key: value for key, value in kwargs.items() if value is not None}
            generated_item_names = [name for name in ["categories", "users", "services", "bookings", "rolechanges"] if
                                    name in specified]

            for _name in generated_item_names:
                count = kwargs.get(_name)
                getattr(self, f"_generate_{_name}")(count)
