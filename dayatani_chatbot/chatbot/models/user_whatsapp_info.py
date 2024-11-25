from django.db import models
from .base import BaseModel
from .user import User


class UserWhatsappInfo(BaseModel):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=400, null=True, blank=True)
    profession = models.CharField(max_length=400, null=True, blank=True)
    land_size = models.CharField(max_length=400, null=True, blank=True)
    crop_growing = models.CharField(max_length=400, null=True, blank=True)
    soil_type = models.CharField(max_length=400, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    unsubscribe = models.BooleanField(default=False)

    @property
    def location(self):
        if self.latitude != None and self.longitude != None:
            return f"latitude={self.latitude},longitude={self.longitude}"
        else:
            return None