from django.db import models
from .base import BaseModel

class WhatsappCronContent(BaseModel):
    link = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=800)
    content_type = models.CharField(max_length=50)
    is_sent = models.BooleanField(default=False)