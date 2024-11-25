
from django.db import models
from .base import BaseModel
from .file_batch import FileBatch
from .files import Files

class FileTrainingStatus(BaseModel):
    batch = models.ForeignKey(FileBatch, on_delete=models.DO_NOTHING)
    file = models.ForeignKey(Files, on_delete=models.DO_NOTHING, null=True)
    processed = models.BooleanField(default=False) 
     