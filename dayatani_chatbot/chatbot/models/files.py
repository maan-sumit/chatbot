from django.db import models
from .base import BaseModel
from .user import User

class Files(BaseModel):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=300, null=True)
    url = models.URLField(null=True, max_length=400)
    status = models.CharField(max_length=100, null=True)
    is_deleted = models.BooleanField(default=False)
