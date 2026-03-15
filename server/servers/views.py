from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from .models import MinecraftServer
from .serializers import MinecraftServerSerializer
from .orchestrator import orchestrate_server_action
import os
import re

@api_view(['POST'])
def create_and_start_server(request):
    server_name = request.data.get('server_name', '')
    if not re.match(r'^[a-zA-Z0-9_-]+$', server_name):
        return Response(
            {"error": "Server name can only contain letters, numbers, hyphens and underscroes"},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = MinecraftServerSerializer(data=request.data)

    if serializer.is_valid():
        raw_password = serializer.validated_data.get('server_password')
        hashed_password = make_password(raw_password)

        server_instance = serializer.save(server_password=hashed_password, is_running=True)

        success, message = orchestrate_server_action(server_instance.id, "START")

        if success:
            return Response({
                "message": "Server Booted successfully!",
                "server": MinecraftServerSerializer(server_instance).data,
            }, status=status.HTTP_201_CREATED)
        
        else:
            server_instance.delete()
            return Response(
                {"error": message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def restart_server(request):
    server_name = request.data.get('server_name')
    password = request.data.get('server_password')

    try:
        server_instance = MinecraftServer.objects.get(server_name=server_name)

    except MinecraftServer.DoesNotExist:
        return Response({"error": "Server Not Found."}, status=status.HTTP_404_NOT_FOUND)
    
    if not check_password(password, server_instance.server_password):
        return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)
    
    if server_instance.is_running:
        return Response({"error": "Server is already running in AWS!"}, status=status.HTTP_400_BAD_REQUEST)
    
    server_instance.status = 'PROVISIONING'
    server_instance.servre_ip = None
    server_instance.save()

    success, message = orchestrate_server_action(server_instance.id, "START")

    if success:
        return Response({
            "message": "Server Restarted Successfully",
            "server": MinecraftServerSerializer(server_instance).data,
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "message": message,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def list_servers(request):
    servers = MinecraftServer.objects.all().order_by('-created_at')
    serializer = MinecraftServerSerializer(servers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
def webhook_update_status(request):
    received_secret = request.data.get('webhook_secret')
    expected_secret = os.environ.get('WEBHOOK_SECRET')

    if received_secret != expected_secret:
        return Response({"error": "Unauthorized Webhook"}, status=status.HTTP_401_UNAUTHORIZED)
    
    server_name = request.data.get('server_name')

    try:
        server = MinecraftServer.objects.get(server_name=server_name)

        new_status = request.data.get('status')
        
        if request.data.get('ip_address'):
            server.server_ip = request.data.get('ip_address')
            server.is_running = True
        elif new_status == 'OFFLINE':
            server.is_running = False
            server.server_ip = None
            server.status = 'OFFLINE'
        elif new_status in ['INSTALLING', 'STARTING', 'BOOTING', 'ONLINE']:
            server.status = new_status

        server.save()
        return Response({"message": "Status updated successfully via webhook!"}, status=status.HTTP_200_OK)
    except MinecraftServer.DoesNotExist:
        return Response({"error": "Server Not Found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST', 'DELETE'])
def delete_servers(request, pk=None):
    if request.method == 'POST':
        server_name = request.data.get('server_name')
        password = request.data.get('server_password')
        try:
            server_instance = MinecraftServer.objects.get(server_name=server_name)
            if not check_password(password, server_instance.server_password):
                return Response({"error": "Incorrect Password"}, status=status.HTTP_400_BAD_REQUEST)
        except MinecraftServer.DoesNotExist:
            return Response({"error": "Server Not Found"}, status=status.HTTP_404_NOT_FOUND)
    else:
        try:
            server_instance = MinecraftServer.objects.get(pk=pk)
        except MinecraftServer.DoesNotExist:
            return Response({"error": "Server Not Found"}, status=status.HTTP_404_NOT_FOUND)
        
    orchestrate_server_action(server_instance.id, "STOP")

    server_instance.delete()
    return Response({"message": "Server deleted successfully!"}, status=status.HTTP_200_OK)