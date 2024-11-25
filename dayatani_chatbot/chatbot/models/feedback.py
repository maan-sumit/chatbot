from django.db import models
from .base import BaseModel
from .conversation import Conversation
from .conversation_detail import ConversationDetail

class Feedback(BaseModel):
    like = models.BooleanField(default=False)
    feedback = models.TextField(null=True)
    conversation_detail = models.ForeignKey(ConversationDetail, on_delete=models.DO_NOTHING)


    def __str__(self):
        return str(self.feedback) if self.feedback else ''