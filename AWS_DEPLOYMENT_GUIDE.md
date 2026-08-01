# AWS Docker Deployment Guide for NovaTech Website

This guide walks you through building your Docker container and deploying it on AWS using **AWS App Runner** (Easiest & recommended for Flask) or **AWS ECS Fargate**.

---

## 1. Test Docker Container Locally

Before deploying to AWS, test the container locally on your computer:

```bash
# Build the Docker image
docker build -t novatech-web .

# Run the Docker container
docker run -p 8000:8000 --env-file .env novatech-web
```

Or using Docker Compose:

```bash
docker-compose up --build
```

Access the application at `http://localhost:8000`.

---

## 2. Push Image to AWS ECR (Elastic Container Registry)

### Step 2.1: Authenticate Docker to AWS ECR
Replace `<AWS_ACCOUNT_ID>` and `<REGION>` (e.g., `us-east-1`):

```bash
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com
```

### Step 2.2: Create ECR Repository
```bash
aws ecr create-repository --repository-name novatech-web --region <REGION>
```

### Step 2.3: Tag and Push
```bash
docker tag novatech-web:latest <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/novatech-web:latest

docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/novatech-web:latest
```

---

## 3. Option A: Deploy on AWS App Runner (Recommended / Easiest)

AWS App Runner manages container deployment, scaling, and SSL automatically.

1. Open **AWS App Runner Console** -> Click **Create Service**.
2. **Source**: Select **Container Registry** -> **Amazon ECR**.
3. Choose repository `novatech-web` and tag `latest`.
4. **Deployment Trigger**: Select **Automatic** (auto-deploys when pushing new image tags).
5. **Configuration**:
   - Port: `8000`
   - CPU & Memory: `1 vCPU / 2 GB RAM`
   - Environment Variables (Add your secrets from `.env`):
     - `SECRET_KEY`
     - `JWT_SECRET_KEY`
     - `ADMIN_USERNAME`
     - `ADMIN_PASSWORD`
     - `DATABASE_URL`
     - `RESEND_API_KEY`
     - `RECEIVER_EMAIL`
6. Click **Create & Deploy**. AWS App Runner will provide your live HTTPS URL.

---

## 4. Option B: Deploy on AWS ECS Fargate

1. **Create ECS Cluster**: AWS Console -> ECS -> Create Cluster (AWS Fargate).
2. **Create Task Definition**:
   - Launch type: `Fargate`
   - Container Image: `<AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/novatech-web:latest`
   - Port mappings: `8000` TCP
   - Environment variables: Configure `.env` values or AWS Secrets Manager.
3. **Create Service**:
   - Attach Application Load Balancer (ALB) on port `80`/`443`.
   - Set target group health check path to `/`.

---

## Environment Variables Checklist

Ensure these key variables are set in your AWS service configuration:

| Variable | Description |
| --- | --- |
| `PORT` | Container listening port (`8000`) |
| `SECRET_KEY` | Flask session secret key |
| `JWT_SECRET_KEY` | Secret key for JWT admin tokens |
| `ADMIN_USERNAME` | Admin login username |
| `ADMIN_PASSWORD` | Admin login password |
| `DATABASE_URL` | PostgreSQL / Neon DB Connection String |
| `RESEND_API_KEY` | Resend API key for email delivery |
| `RECEIVER_EMAIL` | Target email for contact form notifications |
