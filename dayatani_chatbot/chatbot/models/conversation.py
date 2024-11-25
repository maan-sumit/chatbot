from django.db import models
from .base import BaseModel
from .user import User
from datetime import datetime

class Conversation(BaseModel):

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='conversation')
    heading = models.TextField(null=True)
    answer = models.TextField(null=True)
    conversation_detail_modified_at = models.DateTimeField(default=datetime.now)
    whatsapp_chat = models.BooleanField(default=False)

    def __str__(self):
        return self.heading if self.heading else str(self.id)