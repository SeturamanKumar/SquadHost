from django.db import models
import uuid

class MinecraftServer(models.Model):

    STATUS_CHOICES = [
        ('PROVISIONING', 'Provisioning EC2'),
        ('INSTALLING', 'Installing Dependencies'),
        ('STARTING', 'Starting Container'),
        ('BOOTING', 'Booting Minecraft'),
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
    ]
    
    RAM_CHOICES = [
        (2, '2GB - Small (1-4 Players) ~0.02$/hour'),
        (4, '4GB - Medium (4-10 Players) ~0.04$/hour'),
        (8, '8GB - Large (10-20 Players) ~0.08$/hour'),
        (16, '16GB - Extra Large (Modded or for upto 40 Players) ~0.17$/hour'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    server_name = models.CharField(max_length=100, unique=True)
    server_password = models.CharField(max_length=128)

    mc_version = models.CharField(max_length=20, default="LATEST")
    difficulty = models.CharField(max_length=20, default="normal")
    max_players = models.IntegerField(default=20)
    allow_tlauncher = models.BooleanField(default=False)
    seed = models.CharField(max_length=255, null=True, blank=True)

    server_ip = models.CharField(max_length=50, null=True, blank=True)
    container_id = models.CharField(max_length=100, null=True, blank=True)
    is_running = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROVISIONING')
    ram = models.IntegerField(choices=RAM_CHOICES, default=4)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.server_name
