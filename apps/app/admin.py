from django.contrib import admin
from .models import Park

class ParkAdmin(admin.ModelAdmin):
    list_display = ("name", "lat", "lng", "size")

admin.site.register(Park, ParkAdmin)
