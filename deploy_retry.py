import paramiko
import time

IP = '23.94.223.224'
USER = 'root'
PASSWORD = 'cs5Z9qiwG3UQG0a33J'
REMOTE_DIR = '/opt/aiwar_online'

def run_cmd(client, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    err = stderr.read().decode()
    if err:
        print(f"Error: {err}")
    return stdout.channel.recv_exit_status()

def main():
    print("Connecting to SSH...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(IP, username=USER, password=PASSWORD)
    
    print("Re-building Docker Image...")
    # Using docker buildx if docker build fails, or just standard docker build
    run_cmd(client, f"cd {REMOTE_DIR} && docker build -t aiwar-app .")
    
    print("Starting Docker Container...")
    run_cmd(client, "docker stop aiwar-container")
    run_cmd(client, "docker rm aiwar-container")
    run_cmd(client, f"cd {REMOTE_DIR} && docker run -d --name aiwar-container --restart always -p 15000:15000 aiwar-app")
    
    print("Deployment completed successfully!")
    client.close()

if __name__ == "__main__":
    main()
