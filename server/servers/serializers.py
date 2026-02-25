from rest_framework import serializers
from .models import MinecraftServer

class MinecraftServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinecraftServer
        fields = [
            'id',
            'server_name',
            'mc_version',
            'difficulty',
            'max_players',
            'allow_tlauncher',
            'port_number',
            'is_running',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'port_number',
            'is_running',
            'created_at',
        ]