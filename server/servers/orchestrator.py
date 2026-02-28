import docker
import time

def start_minecraft_server(server_name, port_number, mc_version="LATEST", allow_tlauncher=False, max_players=10, difficulty="normal", seed=None):
    try:
        client = docker.from_env()
    except Exception as e:
        print(f"CRITICAL ERROR: Docker is not running! Details: {e}")
        return None

    print(f"Preparing to start {server_name} on port {port_number}")

    env_vars = {
        "EULA": "TRUE",
        "TYPE": "PAPER",
        "MEMORY": "1G",
        "VERSION": mc_version,
        "MAX_PLAYERS": str(max_players),
        "DIFFICULTY": difficulty,
        "ENABLE_AUTOSTOP": "TRUE",
        "AUTOSTOP_TIMEOUT_EST": "300",
        "AUTOSTOP_TIMEOUT_INIT": "300",
    }

    if seed:
        env_vars["SEED"] = seed

    if allow_tlauncher:
        env_vars["ONLINE_MODE"] = "FALSE"
        print("Tlauncher support enabled (Online Mode: OFF)")
    else:
        env_vars["ONLINE_MODE"] = "TRUE"
        print("Official Mojang authentication enable (Online Mode: On)")

    try:
        container = client.containers.run(
            "itzg/minecraft-server",
            name=server_name,
            detach=True,
            environment=env_vars,
            ports={'25565/tcp': port_number},
            volumes={
                f'squadhost_{server_name}': {'bind': '/data', 'mode': 'rw'},
            },
            auto_remove=True,
        )

        print(f"Success! Container {container.short_id} is booting with max {max_players} players on {difficulty} difficulty.")
        return container
    
    except docker.errors.APIError as e:
        print(f"Failed to start container: {e}")
        return None
    
def stop_minecraft_server(container):
    print(f"Sending stop command to {container.name}...")
    container.stop(timeout=30)
    print("Server gracefully stopped and completely removed")

if __name__ == "__main__":
    print("--- SquadHost Interactive Engine Test ---")

    test_container =  start_minecraft_server(
        server_name="squadhost_custom_01",
        port_number=25570,
        mc_version="1.20.4",
        allow_tlauncher=True,
        max_players=5,
        difficulty="hard",
    )

    if test_container:
        print("Letting the custom server generate for 15 seconds")
        time.sleep(15)

        input("\n>> SERVER IS BOOTING! Open Minecraft (v1.20.4). \n>> Connect to IP: localhost:25570 \n>> Press ENTER in this terminal ONLY when you are ready to shut it down and delete the server...\n")

        stop_minecraft_server(test_container)
        print("Custom server test complete")