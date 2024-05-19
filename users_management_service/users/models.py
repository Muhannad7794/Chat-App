from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class CustomUser(AbstractUser):
    verification_code = models.CharField(max_length=100, blank=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.verification_code:
            # Generate verification code only once when the user is created
            self.verification_code = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
