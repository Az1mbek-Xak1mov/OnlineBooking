from django import forms
from django.contrib import admin

from .models import Park


class LeafletLocationWidget(forms.Widget):
    template_name = "apps/widgets/leaflet_location.html"

    class Media:
        css = {"all": ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",)}
        js = ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",)

    def __init__(self, attrs=None, lat_field="lat", lon_field="lng"):
        self.lat_field = lat_field
        self.lon_field = lon_field
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["lat"] = self.lat_field
        context["lng"] = self.lon_field
        return context


class ParkModelForm(forms.ModelForm):
    location_map = forms.Field(
        required=False,
        widget=LeafletLocationWidget(lat_field="lat", lon_field="lng"),
        label="Map",
    )

    class Meta:
        model = Park
        fields = "__all__"
        widgets = {
            "lat": forms.NumberInput(attrs={"step": "any"}),
            "lng": forms.NumberInput(attrs={"step": "any"}),
        }


@admin.register(Park)
class ParkAdmin(admin.ModelAdmin):
    list_display = ("name", "lat", "lng", "size")
    form = ParkModelForm

    fieldsets = (
        (None, {
            "fields": ("name", "lat", "lng")
        }),
        ("Location Map", {
            "fields": ("location_map",),
        }),
    )
