
from django.db import models
from .base import BaseModel
from .user import User

class Logs(BaseModel):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    activity = models.CharField(max_length=200)
    file_url = models.TextField(null=True)
