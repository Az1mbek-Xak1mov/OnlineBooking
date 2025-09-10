from django.db.models import (CASCADE, SET_NULL, CharField,
                              DateField, ForeignKey, PositiveIntegerField, TimeField)

from apps.shared.models import UUIDBaseModel, CreatedBaseModel


class ServiceCategory(UUIDBaseModel, CreatedBaseModel):
    name = CharField(max_length=255)

    def __str__(self):
        return self.name


class Service(UUIDBaseModel, CreatedBaseModel):
    user = ForeignKey('authentication.User', CASCADE, limit_choices_to={'type': 'provider'},
                      related_name="services")  # TODO change name
    category = ForeignKey('app.ServiceCategory', SET_NULL, null=True, related_name="services")
    name = CharField(max_length=255)
    address = CharField(max_length=255)
    # TODO location
    capacity = PositiveIntegerField(default=1)

    def __str__(self):
        return self.name


class Schedule(UUIDBaseModel, CreatedBaseModel):  # TODO fix
    service = ForeignKey('app.Service', CASCADE, related_name="schedules")
    date = DateField()
    start_time = TimeField()
    end_time = TimeField()

    def __str__(self):
        return f"{self.service.name} - {self.date} ({self.start_time}-{self.end_time})"


class ServiceSchedule(UUIDBaseModel, CreatedBaseModel):  # TODO fix
    service = ForeignKey(Service, CASCADE, related_name="service_schedules")
    schedule = ForeignKey(Schedule, CASCADE, related_name="service_schedules")

    def __str__(self):
        return f"{self.service.name} -> {self.schedule.date}"


class Booking(UUIDBaseModel, CreatedBaseModel):
    service = ForeignKey('app.Service', CASCADE, related_name="bookings")
    user = ForeignKey('authentication.User', CASCADE, related_name="bookings")
    date = DateField()
    start_time = TimeField()  # 18:00
    end_time = TimeField()  # 20:00
    seats = PositiveIntegerField(db_default=1)

    def __str__(self):
        return (f"{self.user.phone_number} -> "
                f"{self.service.name} ({self.start_time.strftime('%H:%M')}, {self.seats} joy)")
