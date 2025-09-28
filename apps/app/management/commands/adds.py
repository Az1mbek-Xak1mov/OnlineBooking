import random
import re
from datetime import time, timedelta

from app.models import (Booking, Service, ServiceCategory, ServiceSchedule,
                        WeekdayChoices)
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
        self.faker = Faker("uz_UZ")
        for _ in range(number):
            while True:
                phone_number = ''.join(re.findall(r"\d", self.faker.phone_number()))
                if not User.objects.filter(phone_number=phone_number).exists():
                    break

            User.objects.create_user(
                phone_number=phone_number,
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                type=random.choice(User.Type.choices)[0],
                telegram_id=random.randint(10000000, 99999999),
                password="1",
            )

        self.stdout.write(self.style.SUCCESS(f"Users generated - {number}"))

    def _generate_categories(self, number: int = 5):
        for _ in range(number):
            ServiceCategory.objects.create(name=self.faker.word().capitalize())
        self.stdout.write(self.style.SUCCESS(f"Categories generated - {number}"))

    def _generate_services(self, number: int = 5):

        providers_ids = User.objects.filter(type=User.Type.PROVIDER).values_list('id', flat=True)
        categories_id = ServiceCategory.objects.values_list('id', flat=True)

        if not providers_ids or not categories_id:
            self.stdout.write(self.style.ERROR("No providers or categories"))
            return

        for _ in range(number):
            is_deleted = self.faker.random.choice([True, False])
            service = Service.objects.create(
                owner_id=self.faker.random.choice(providers_ids),
                category_id=self.faker.random.choice(categories_id),
                name=self.faker.company(),
                address=self.faker.address(),
                capacity=self.faker.random.randint(1, 20),
                duration=timedelta(minutes=self.faker.random.choice([30, 60, 120])),
                price=self.faker.random.randint(10000, 100000),
                description=self.faker.text(),
                is_deleted=is_deleted
            )
            # schedules
            for day, _ in WeekdayChoices.choices:
                if self.faker.random.choice([True, False]):
                    start = time(hour=random.randint(8, 18), minute=0)
                    end = (timezone.datetime.combine(timezone.now(), start) + timedelta(hours=2)).time()
                    ServiceSchedule.objects.create(
                        service=service,
                        weekday=day,
                        start_time=start,
                        end_time=end,
                    )

        self.stdout.write(self.style.SUCCESS(f"Services generated - {number}"))


    def _generate_bookings(self, number: int = 5):
        customers_id = list(User.objects.filter(type=User.Type.CUSTOMER).values_list('id', flat=True))
        services = list(Service.objects.all())

        if not customers_id or not services:
            self.stdout.write(self.style.ERROR("No customers or services"))
            return

        for _ in range(number):
            service = random.choice(services)
            user_id = random.choice(customers_id)
            weekday = random.choice(WeekdayChoices.values)
            date = timezone.localdate() + timedelta(days=random.randint(0, 14))

            # Случайное время начала между 9 и 17 часами
            start_time = time(hour=random.randint(9, 17), minute=0)

            # Определяем duration — кратный service.duration (например, 1x, 2x, 3x)
            multiplier = random.randint(1, 3)
            duration = service.duration * multiplier

            # seats — не больше вместимости
            seats = random.randint(1, min(5, service.capacity))

            Booking.objects.create(
                service=service,
                weekday=weekday,
                user_id=user_id,
                date=date,
                start_time=start_time,
                duration=duration,
                seats=seats,
            )

        self.stdout.write(self.style.SUCCESS(f"Bookings generated - {number}"))

    def _generate_rolechanges(self, number: int = 5):
        customers_id = User.objects.filter(type=User.Type.CUSTOMER).values_list('id', flat=True)

        if not customers_id:
            self.stdout.write(self.style.ERROR("No customers for role change requests"))
            return

        for _ in range(number):
            user = self.faker.random.choice(customers_id)
            is_read = self.faker.random.choice([True, False])
            is_accepted = self.faker.random.choice([True, False]) if is_read else None

            RoleChange.objects.create(
                user_id=user,
                message=self.faker.sentence(),
                is_read=is_read,
                is_accepted=is_accepted,
            )

        self.stdout.write(self.style.SUCCESS(f"RoleChange requests generated - {number}"))

    def handle(self, *args, **kwargs):
        self.faker = Faker('uz_Uz')

        if kwargs.get('all'):
            generated_item_names = self.model_list
        else:
            kwargs = {key: value for key, value in kwargs.items() if value is not None}
            generated_item_names = set(kwargs).intersection(self.model_list)

        for _name in generated_item_names:
            if kwargs[_name] is None:
                getattr(self, f"_generate_{_name}")()
            else:
                getattr(self, f"_generate_{_name}")(kwargs[_name])
