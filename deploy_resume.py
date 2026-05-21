import paramiko

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
    client.get_transport().set_keepalive(15)
    
    print("Starting Docker Container...")
    run_cmd(client, "docker stop aiwar-container")
    run_cmd(client, "docker rm aiwar-container")
    run_cmd(client, f"cd {REMOTE_DIR} && docker run -d --name aiwar-container --restart always -p 15000:15000 aiwar-app")
    
    print("Configuring Nginx...")
    nginx_conf = """
server {
    listen 80;
    server_name deermiya.com www.deermiya.com;

    location / {
        proxy_pass http://127.0.0.1:15000;
        proxy_set_header Host $host;
        
        # 传递 Cloudflare 提供的真实客户端 IP
        proxy_set_header X-Real-IP $http_cf_connecting_ip;
        proxy_set_header X-Forwarded-For $http_cf_connecting_ip;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
    cmd_write = f"cat << 'EOF' > /etc/nginx/sites-available/deermiya.com\n{nginx_conf}\nEOF"
    run_cmd(client, cmd_write)
    run_cmd(client, "ln -sf /etc/nginx/sites-available/deermiya.com /etc/nginx/sites-enabled/")
    run_cmd(client, "rm -f /etc/nginx/sites-enabled/default")
    run_cmd(client, "systemctl reload nginx")
    
    print("Deployment completed successfully!")
    client.close()

if __name__ == "__main__":
    main()
