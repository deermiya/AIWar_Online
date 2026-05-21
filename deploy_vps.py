import paramiko
import os
import zipfile

IP = '23.94.223.224'
USER = 'root'
PASSWORD = 'cs5Z9qiwG3UQG0a33J'
LOCAL_DIR = r'd:\Project\AIWar_Online'
REMOTE_DIR = '/opt/aiwar_online'
ZIP_NAME = 'aiwar.zip'

def run_cmd(client, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    err = stderr.read().decode()
    if err:
        print(f"Error: {err}")
    return stdout.channel.recv_exit_status()

def zip_dir(local_dir, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(local_dir):
            if '.git' in root or '__pycache__' in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                if file_path == zip_path:
                    continue
                arcname = os.path.relpath(file_path, local_dir)
                zipf.write(file_path, arcname)

def main():
    zip_path = os.path.join(LOCAL_DIR, ZIP_NAME)
    print("Zipping files...")
    zip_dir(LOCAL_DIR, zip_path)
    
    print("Connecting to SSH...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(IP, username=USER, password=PASSWORD)
    
    print("Installing unzip, Docker & Nginx...")
    run_cmd(client, "apt-get install -y unzip docker.io nginx")
    
    print("Uploading project files...")
    sftp = client.open_sftp()
    remote_zip = f"/opt/{ZIP_NAME}"
    sftp.put(zip_path, remote_zip)
    sftp.close()
    
    print("Unzipping files...")
    run_cmd(client, f"mkdir -p {REMOTE_DIR} && unzip -o {remote_zip} -d {REMOTE_DIR}")
    
    print("Building Docker Image...")
    run_cmd(client, f"cd {REMOTE_DIR} && docker build -t aiwar-app .")
    
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
    
    if os.path.exists(zip_path):
        os.remove(zip_path)

if __name__ == "__main__":
    main()
