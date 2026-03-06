from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from .models import MinecraftServer
from .serializers import MinecraftServerSerializer
from .orchestrator import orchestrate_server_action
import os

def get_available_port():
    last_server = MinecraftServer.objects.order_by('-port_number').first()
    if last_server and last_server.port_number:
        return last_server.port_number + 1
    return 25565

@api_view(['POST'])
def create_and_start_server(request):
    serializer = MinecraftServerSerializer(data=request.data)

    if serializer.is_valid():
        raw_password = serializer.validated_data.get('server_password')
        hashed_password = make_password(raw_password)

        server_instance = serializer.save(server_password=hashed_password)
        assigned_port = get_available_port()

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
        return Response({"error": "Server Not Found."}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not check_password(password, server_instance.server_password):
        return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)
    
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
        
        if request.data.get('status'):
            server.status = request.data.get('status')
        if request.data.get('ip_address'):
            server.server_ip = request.data.get('ip_address')

        server.name()
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