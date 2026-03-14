from rest_framework import serializers
from .models import MinecraftServer

class MinecraftServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinecraftServer
        fields = [
            'id',
            'server_name',
            'server_password',
            'mc_version',
            'difficulty',
            'max_players',
            'allow_tlauncher',
            'seed',
            'server_ip',
            'is_running',
            'status',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'is_running',
            'created_at',
        ]
        extra_kwargs = {
            'server_password': {'write_only': True},
        }