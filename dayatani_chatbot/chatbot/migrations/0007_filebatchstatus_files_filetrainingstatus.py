# Generated by Django 3.2 on 2023-09-14 06:42

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0006_merge_20230818_1106'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileBatchStatus',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('batch_id', models.UUIDField()),
                ('abort', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='chatbot.user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileTrainingStatus',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file_name', models.CharField(max_length=200)),
                ('processed', models.BooleanField(default=False)),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='chatbot.filebatchstatus')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Files',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(upload_to='')),
                ('status', models.CharField(max_length=100, null=True)),
                ('archive', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='chatbot.user')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
