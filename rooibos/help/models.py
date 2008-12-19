from django.db import models

class Tooltip(models.Model):
    reference = models.CharField(max_length=100, unique=True, null=False, blank=False)
    tooltip = models.TextField()
    