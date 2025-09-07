import uuid

from django.db import models  # noqa
from django.db.models import CharField, ForeignKey, CASCADE, SET_NULL, PositiveIntegerField, DateField, TimeField, \
    BooleanField, TextChoices
from django.db.models.base import Model
from django.db.models.fields import DateTimeField, UUIDField
from rest_framework.fields import ImageField


# Create your models here.


class UUIDModel(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class CreatedBaseModel(UUIDModel):
    updated_at = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

from django.conf import settings


class ServiceCategory(Model):
    name = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Service(Model):
    user = ForeignKey(settings.AUTH_USER_MODEL,CASCADE,related_name="services")
    category = ForeignKey(ServiceCategory,SET_NULL,null=True,related_name="services")
    name = CharField(max_length=255)
    location = CharField(max_length=255)
    capacity = PositiveIntegerField(default=1)  # Bir vaqtning o‘zida necha odam sig‘adi
    available_places = PositiveIntegerField(default=1)  # Hozirgi mavjud joylar
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"


class Schedule(Model):

    service = ForeignKey(Service, CASCADE, related_name="schedules")
    date = DateField()
    start_time = TimeField()
    end_time = TimeField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service.name} - {self.date} ({self.start_time}-{self.end_time})"


class Calendar(Model):
    date = DateField(unique=True)
    is_day_off = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} - {'Dam olish' if self.is_day_off else 'Ish kuni'}"


class ServiceSchedule(Model):
    service = ForeignKey(Service, CASCADE, related_name="service_schedules")
    schedule = ForeignKey(Schedule, CASCADE, related_name="service_schedules")
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service.name} -> {self.schedule.date}"


class Booking(Model):
    service = ForeignKey(Service, CASCADE, related_name="bookings")
    user = ForeignKey(settings.AUTH_USER_MODEL, CASCADE, related_name="bookings")
    start_time = DateTimeField()  # Boshlanish vaqti
    duration = PositiveIntegerField(default=60)  # qancha vaqt (daqiqada)
    seats = PositiveIntegerField(default=1)  # nechta joy band qildi
    qr_code = ImageField(upload_to="qrcodes/", blank=True, null=True)  # QR code rasmi
    created_at = DateTimeField(auto_now_add=True)

    @property
    def end_time(self):
        """Boshlanish + duration orqali tugash vaqtini hisoblaydi"""
        from django.utils import timezone
        return self.start_time + timezone.timedelta(minutes=self.duration)

    def save(self, *args, **kwargs):
        import qrcode
        from io import BytesIO
        from django.core.files.base import ContentFile

        super().save(*args, **kwargs)  # Avval bookingni saqlash

        if not self.qr_code:
            data = f"BookingID: {self.id}\nService: {self.service.name}\nTime: {self.start_time}\nSeats: {self.seats}"
            qr = qrcode.make(data)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")

            filename = f"booking_qr_{self.id}.png"
            self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
            super().save(update_fields=['qr_code'])

    def __str__(self):
        return f"{self.user.username} -> {self.service.name} ({self.start_time.strftime('%H:%M')}, {self.seats} joy)"
