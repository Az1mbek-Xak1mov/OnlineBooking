# admin_forms.py (or forms.py)
from django import forms
from map_widgets.widgets import LeafletWidget

from .models import Park


class ParkAdminForm(forms.ModelForm):
    location = forms.CharField(required=False, label="Location", widget=LeafletWidget(attrs={
        "data-map-elem-id": "id_location"
    }))

    class Meta:
        model = Park
        fields = ("name", "size", "lat", "lng", "location")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # prefill the map with existing coords
        if self.instance and self.instance.pk:
            if self.instance.lat is not None and self.instance.lng is not None:
                self.fields["location"].initial = f"{self.instance.lat},{self.instance.lng}"

    def clean(self):
        cleaned = super().clean()
        loc = cleaned.get("location")
        if loc:
            # widget usually stores "lat,lng" in the hidden input — be defensive on parsing
            try:
                parts = [p.strip() for p in loc.split(",")]
                if len(parts) >= 2:
                    cleaned["lat"] = float(parts[0])
                    cleaned["lng"] = float(parts[1])
            except Exception:
                raise forms.ValidationError("Could not parse coordinates from the map.")
        return cleaned

    def save(self, commit=True):
        # ensure model lat/lng are set from cleaned data before saving
        if "lat" in self.cleaned_data and "lng" in self.cleaned_data:
            self.instance.lat = self.cleaned_data["lat"]
            self.instance.lng = self.cleaned_data["lng"]
        return super().save(commit=commit)
