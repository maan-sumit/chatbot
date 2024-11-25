from django.db import models
from .base import BaseModel
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# managers.py
from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, mobile_number, password=None, **extra_fields):
        if not mobile_number:
            raise ValueError("The Mobile Number field must be set")
        user = self.model(mobile_number=mobile_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(mobile_number, password, **extra_fields)


class User(BaseModel, AbstractBaseUser):

    name = models.CharField(max_length=64,null= True,blank= True)
    mobile_number = models.CharField(max_length=30, unique=True, null=True)
    sso_uid = models.CharField(max_length=200, null= True,blank= True)
    client_id = models.CharField(max_length=200, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    objects = CustomUserManager()

    USERNAME_FIELD = "mobile_number"

    def __str__(self):
        return str(self.sso_uid)
    
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

