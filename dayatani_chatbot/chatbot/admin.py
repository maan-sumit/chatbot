from django.contrib import admin
from .models import *

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id','sso_uid','mobile_number','name','is_staff','is_active','is_superuser',]
    list_filter = ('updated_at',)


@admin.register(Conversation)
class Conversationadmin(admin.ModelAdmin):
    list_display = [field.name for field in Conversation._meta.fields]


@admin.register(ConversationDetail)
class ConversationDetailAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ConversationDetail._meta.fields]


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Feedback._meta.fields]


@admin.register(Files)
class FileAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Files._meta.fields]


@admin.register(FileBatch)
class FileBatchAdmin(admin.ModelAdmin):
    list_display = [field.name for field in FileBatch._meta.fields]


@admin.register(FileTrainingStatus)
class FileTrainingStatusAdmin(admin.ModelAdmin):
    list_display = [field.name for field in FileTrainingStatus._meta.fields]


@admin.register(Logs)
class LogsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Logs._meta.fields]


