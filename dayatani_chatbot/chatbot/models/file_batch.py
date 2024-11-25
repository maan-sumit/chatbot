from django.db import models
from .base import BaseModel
from .user import User

class FileBatch(BaseModel):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    batch_id = models.UUIDField()
    batch_processed = models.BooleanField(default=False)
    abort = models.BooleanField(default=False)
 