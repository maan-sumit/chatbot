from django.db import models
from .base import BaseModel

class WhatsappFlow(BaseModel):
    flow_id = models.CharField(max_length=255, unique=True)
    flow_name = models.CharField(max_length=50, unique=True)
    cta = models.CharField(max_length=20)