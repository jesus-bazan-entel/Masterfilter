from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from movil.models import Document

# Create your models here.
class ApiKey(models.Model):
    key = models.CharField(max_length=100)
    url = models.CharField(max_length=1024)
    queriesLeft = models.IntegerField(default=0)

    def __str__(self):
        return str(self.key)+" | "+str(self.queriesLeft)

class Consecutive(models.Model):
    active = models.BooleanField(default=True)
    finish = models.BooleanField(default=False)
    file = models.CharField(max_length=150, null=True, blank=True)
    total = models.IntegerField(default=0)
    progres = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    num = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True)

    def __str__(self) -> str:
        return str(self.file)+" | "+str(self.user)

class PhoneNumber(models.Model):
    phone = models.CharField(max_length=100)
    originalOperator = models.CharField(max_length=100)
    originalOperatorRaw = models.CharField(max_length=100)
    currentOperator = models.CharField(max_length=100)
    currentOperatorRaw = models.CharField(max_length=100)
    prefix = models.CharField(max_length=100)
    type_p = models.CharField(max_length=100)
    typeDescription = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    consecutive = models.ForeignKey(Consecutive, on_delete=models.CASCADE, null=True)
    fecha_hora = models.DateTimeField(default=timezone.now, db_index=True)
    when_p = models.CharField(max_length=100, default="")
    from_p = models.CharField(max_length=100, default="")
    fromRaw_p = models.CharField(max_length=100, default="")
    to_p = models.CharField(max_length=100, default="")
    toRaw_p = models.CharField(max_length=100, default="")

    def __str__(self):
        return str(self.phone)+" | "+str(self.currentOperator)+" | "+str(self.when_p)