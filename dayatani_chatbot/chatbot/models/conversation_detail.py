from django.db import models
from .base import BaseModel
from .conversation import Conversation

class ConversationDetail(BaseModel):

    conversation = models.ForeignKey(Conversation, on_delete=models.DO_NOTHING, related_name='conversation_detail')
    conversations = models.TextField(null=True)
    role = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return str(self.conversation)