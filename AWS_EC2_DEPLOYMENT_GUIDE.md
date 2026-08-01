# Complete Guide: Deploying NovaTech Website on AWS EC2 with Docker

This guide details how to deploy your Dockerized Flask application onto an **AWS EC2 Instance** (Ubuntu 22.04 LTS) with **Docker**, **Nginx Reverse Proxy**, and **SSL/TLS (HTTPS)** using Certbot.

---

## Prerequisites
- An active **AWS Account**.
- Your domain name (optional, but needed for HTTPS SSL certificates).

---

## Step 1: Launch an AWS EC2 Instance

1. Log in to the [AWS Management Console](https://console.aws.amazon.com/ec2/).
2. Navigate to **EC2** $\rightarrow$ Click **Launch Instance**.
3. **Name**: `novatech-web-server`.
4. **Application and OS Image (AMI)**: Select **Ubuntu** (Ubuntu Server 22.04 LTS or 24.04 LTS - 64-bit x86).
5. **Instance Type**: `t2.micro` or `t3.micro` (Free Tier eligible).
6. **Key Pair**: Select an existing key pair or click **Create new key pair** (Download the `.pem` file, e.g., `novatech-key.pem`).
7. **Network Settings (Security Group)**:
   - Click **Create Security Group**.
   - Check **Allow SSH traffic** from `Anywhere` (`0.0.0.0/0`) or `My IP`.
   - Check **Allow HTTP traffic from the internet** (`80`).
   - Check **Allow HTTPS traffic from the internet** (`443`).
8. **Configure Storage**: Default `8 GiB` gp3 SSD (or `20 GiB`).
9. Click **Launch Instance**.

---

## Step 2: Connect to your EC2 Instance via SSH

Open your terminal or PowerShell on your local machine and run:

```bash
# Set key permissions (Linux/macOS)
chmod 400 novatech-key.pem

# SSH into EC2 (Replace with your EC2 Public IP address)
ssh -i "novatech-key.pem" ubuntu@<YOUR_EC2_PUBLIC_IP>
```

---

## Step 3: Install Docker & Docker Compose on EC2

Run the following commands to install Docker and Docker Compose using standard Ubuntu packages:

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose

# 3. Start and enable the Docker service
sudo systemctl start docker
sudo systemctl enable docker

# 4. Add ubuntu user to the docker group
sudo usermod -aG docker ubuntu

# 5. Apply user group change
newgrp docker

# 6. Verify Docker installation
docker --version
docker-compose --version
```


---

## Step 4: Transfer Project Files to EC2

### Option A: Via Git (Recommended)
If your code is on GitHub/GitLab:

```bash
git clone https://github.com/your-username/novatech_website.git
cd novatech_website
```

### Option B: Upload via SCP (From your local machine)
Run this command on your **local machine** terminal:

```bash
scp -i "novatech-key.pem" -r e:/project/novatech_website ubuntu@<YOUR_EC2_PUBLIC_IP>:~/novatech_website
```

Then on your EC2 terminal:
```bash
cd ~/novatech_website
```

---

## Step 5: Configure Environment Variables

Create the `.env` file on your EC2 instance:

```bash
nano .env
```

Paste your environment variables:

```env
PORT=8000
SECRET_KEY=your_production_secret_key_here
JWT_SECRET_KEY=your_production_jwt_secret_key_here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_admin_password
DATABASE_URL=postgresql://neondb_owner:npg_DkGxStjs6N7V@ep-misty-leaf-am593szq-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require
RESEND_API_KEY=re_your_resend_api_key
RECEIVER_EMAIL=teckhubofficals@gmail.com
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

---

## Step 6: Build & Run the App with Docker

Run the container using Docker Compose:

```bash
# Build and start container in detached (background) mode
docker compose up --build -d

# Check running containers
docker ps

# View live application logs
docker compose logs -f
```

Your app is now running on port `8000` inside your EC2 instance!

---

## Step 7: Configure Nginx as Reverse Proxy (Port 80 $\rightarrow$ Port 8000)

To serve your website on standard HTTP port `80` (and HTTPS `443`):

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/novatech
```

Paste the following configuration:

```nginx
server {
    listen 80;
    server_name <YOUR_EC2_PUBLIC_IP_OR_DOMAIN>;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the configuration and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/novatech /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

Now open your web browser and visit `http://<YOUR_EC2_PUBLIC_IP>`. Your site is live!

---

## Step 8: (Optional) Set up Free SSL Certificate (HTTPS)

If you pointed a domain name (e.g. `example.com`) to your EC2 Public IP:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will automatically issue an SSL certificate and configure HTTPS redirect!

---

## Useful Commands for Maintenance

- **Restart Application**: `docker compose restart`
- **Rebuild Container**: `docker compose up --build -d`
- **Check Logs**: `docker compose logs -f`
- **Stop Application**: `docker compose down`
