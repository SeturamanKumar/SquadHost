from django.db import models
import uuid

class MinecraftServer(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    server_name = models.CharField(max_length=100, unique=True)
    server_password = models.CharField(max_length=128)

    mc_version = models.CharField(max_length=20, default="LATEST")
    difficulty = models.CharField(max_length=20, default="normal")
    max_players = models.IntegerField(default=20)
    allow_tlauncher = models.BooleanField(default=False)

    seed = models.CharField(max_length=255, null=True, blank=True)

    port_number = models.IntegerField(unique=True, null=True, blank=True)
    container_id = models.CharField(max_length=100, null=True, blank=True)
    is_running = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.server_name