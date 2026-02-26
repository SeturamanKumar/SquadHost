from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from .models import MinecraftServer
from .serializers import MinecraftServerSerializer
from .orchestrator import start_minecraft_server
import docker

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

        container = start_minecraft_server(
            server_name=server_instance.server_name,
            port_number=assigned_port,
            mc_version=server_instance.mc_version,
            allow_tlauncher=server_instance.allow_tlauncher,
            max_players=server_instance.max_players,
            difficulty=server_instance.difficulty,
        )

        if container:
            server_instance.port_number = assigned_port
            server_instance.container_id = container.short_id
            server_instance.is_running = True
            server_instance.save()

            return Response({
                "message": "Server Booted successfully!",
                "server": MinecraftServerSerializer(server_instance).data,
            }, status=status.HTTP_201_CREATED)
        
        else:
            server_instance.delete()
            return Response(
                {"error": "Docker failed to start the container"},
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
    
    if server_instance.is_running and server_instance.container_id:
        try:
            client = docker.from_env()
            container = client.containers.get(server_instance.container_id)

            if container.status == 'running':
                return Response({
                    "message": "Server is already running",
                    "port": server_instance.port_number
                }, status=status.HTTP_200_OK)
            
        except docker.errors.NotFound:
            pass
        except Exception as e:
            pass
    
    assigned_port = get_available_port()

    container = start_minecraft_server(
        server_name=server_instance.server_name,
        port_number=server_instance.port_number,
        mc_version=server_instance.mc_version,
        allow_tlauncher=server_instance.allow_tlauncher,
        max_players=server_instance.max_players,
        difficulty=server_instance.difficulty,
    )

    if container:
        server_instance.container_id = container.short_id
        server_instance.is_running = True
        server_instance.save()

        return Response({
            "message": "Server Restarted Successfully!!!",
            "server": MinecraftServerSerializer(server_instance).data,
        }, status=status.HTTP_200_OK)
    
    else:
        return Response({
            "error": "Docker failed to start the container",
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)