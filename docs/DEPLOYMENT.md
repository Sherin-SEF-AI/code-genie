# CodeGenie Deployment Guide

## Table of Contents
1. [Local Deployment](#local-deployment)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [AWS Deployment](#aws-deployment)
5. [Production Best Practices](#production-best-practices)

## Local Deployment

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/codegenie.git
cd codegenie

# Run installation script
./scripts/install.sh
```

The installation script will:
- Check Python and Ollama installation
- Install required models
- Create virtual environment
- Install CodeGenie
- Create default configuration

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install CodeGenie
pip install -e .

# Start Ollama
ollama serve &

# Pull models
ollama pull llama3.1:8b
ollama pull codellama:7b

# Start CodeGenie
codegenie
```

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/your-org/codegenie.git
cd codegenie

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Using Docker Directly

```bash
# Build image
docker build -t codegenie:latest .

# Run container
docker run -d \
  --name codegenie \
  -p 8000:8000 \
  -p 11434:11434 \
  -v $(pwd)/projects:/workspace \
  -v codegenie-config:/root/.config/codegenie \
  -v codegenie-cache:/root/.cache/codegenie \
  -v ollama-models:/root/.ollama \
  -e OLLAMA_MODELS="llama3.1:8b,codellama:7b" \
  codegenie:latest

# View logs
docker logs -f codegenie

# Stop container
docker stop codegenie
```

### Docker Configuration

Create a `.env` file:

```env
# Environment
CODEGENIE_ENV=production

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODELS=llama3.1:8b,codellama:7b

# Database
POSTGRES_HOST=postgres
POSTGRES_DB=codegenie
POSTGRES_USER=codegenie
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Resources
MAX_MEMORY=16G
MAX_CPU=4
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Persistent storage provisioner
- At least 100GB storage for models

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace codegenie

# Create secrets
kubectl create secret generic codegenie-secrets \
  --from-literal=postgres-password=secure_password \
  -n codegenie

# Apply deployment
kubectl apply -f deploy/kubernetes/deployment.yaml -n codegenie

# Check status
kubectl get pods -n codegenie
kubectl get services -n codegenie

# View logs
kubectl logs -f deployment/codegenie -n codegenie
```

### Scale Deployment

```bash
# Scale to 3 replicas
kubectl scale deployment codegenie --replicas=3 -n codegenie

# Auto-scaling
kubectl autoscale deployment codegenie \
  --min=2 \
  --max=10 \
  --cpu-percent=70 \
  -n codegenie
```

### Update Deployment

```bash
# Update image
kubectl set image deployment/codegenie \
  codegenie=codegenie:v0.3.0 \
  -n codegenie

# Rollback if needed
kubectl rollout undo deployment/codegenie -n codegenie

# Check rollout status
kubectl rollout status deployment/codegenie -n codegenie
```

## AWS Deployment

### Using CloudFormation

```bash
# Deploy stack
aws cloudformation create-stack \
  --stack-name codegenie \
  --template-body file://deploy/aws/cloudformation.yaml \
  --parameters \
    ParameterKey=InstanceType,ParameterValue=g4dn.xlarge \
    ParameterKey=KeyName,ParameterValue=your-key-pair \
    ParameterKey=VpcId,ParameterValue=vpc-xxxxx \
    ParameterKey=SubnetId,ParameterValue=subnet-xxxxx \
  --capabilities CAPABILITY_IAM

# Check status
aws cloudformation describe-stacks \
  --stack-name codegenie \
  --query 'Stacks[0].StackStatus'

# Get outputs
aws cloudformation describe-stacks \
  --stack-name codegenie \
  --query 'Stacks[0].Outputs'
```

### Using EC2 Directly

```bash
# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-xxxxx \
  --instance-type g4dn.xlarge \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxx \
  --subnet-id subnet-xxxxx \
  --user-data file://scripts/ec2-userdata.sh

# SSH to instance
ssh -i your-key.pem ubuntu@<instance-ip>

# Install CodeGenie
curl -fsSL https://raw.githubusercontent.com/your-org/codegenie/main/scripts/install.sh | bash
```

### Using ECS

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name codegenie

# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://deploy/aws/ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster codegenie \
  --service-name codegenie-service \
  --task-definition codegenie:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

## Production Best Practices

### Security

1. **Use HTTPS**
```bash
# Generate SSL certificate
certbot certonly --standalone -d codegenie.example.com

# Configure nginx
server {
    listen 443 ssl;
    server_name codegenie.example.com;
    
    ssl_certificate /etc/letsencrypt/live/codegenie.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/codegenie.example.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. **Enable Authentication**
```yaml
# config.yaml
security:
  authentication:
    enabled: true
    type: "jwt"
    secret_key: "${JWT_SECRET}"
  
  rate_limiting:
    enabled: true
    requests_per_minute: 60
```

3. **Use Secrets Management**
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name codegenie/postgres-password \
  --secret-string "secure_password"

# Kubernetes Secrets
kubectl create secret generic codegenie-secrets \
  --from-literal=postgres-password=secure_password
```

### Performance

1. **Enable Caching**
```yaml
cache:
  enabled: true
  backend: "redis"
  redis_url: "redis://localhost:6379"
  ttl: 3600
```

2. **Use GPU Acceleration**
```yaml
models:
  use_gpu: true
  gpu_memory_fraction: 0.8
```

3. **Configure Resource Limits**
```yaml
resources:
  max_memory: "16GB"
  max_cpu: 4
  max_concurrent_tasks: 10
```

### Monitoring

1. **Enable Logging**
```yaml
logging:
  level: "INFO"
  format: "json"
  outputs:
    - type: "file"
      path: "/var/log/codegenie/app.log"
    - type: "cloudwatch"
      log_group: "/aws/codegenie"
```

2. **Configure Metrics**
```yaml
monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
  cloudwatch:
    enabled: true
    namespace: "CodeGenie"
```

3. **Set Up Alerts**
```yaml
alerts:
  - name: "high_memory"
    condition: "memory_usage > 90%"
    action: "email"
    recipients: ["admin@example.com"]
  
  - name: "high_error_rate"
    condition: "error_rate > 5%"
    action: "slack"
    webhook: "https://hooks.slack.com/..."
```

### Backup and Recovery

1. **Automated Backups**
```bash
# Create backup script
cat > /usr/local/bin/backup-codegenie.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/codegenie/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup config
cp -r ~/.config/codegenie "$BACKUP_DIR/config"

# Backup sessions
cp -r ~/.codegenie/sessions "$BACKUP_DIR/sessions"

# Backup database
pg_dump codegenie > "$BACKUP_DIR/database.sql"

# Upload to S3
aws s3 sync "$BACKUP_DIR" s3://my-backups/codegenie/$(date +%Y%m%d)
EOF

chmod +x /usr/local/bin/backup-codegenie.sh

# Schedule with cron
echo "0 2 * * * /usr/local/bin/backup-codegenie.sh" | crontab -
```

2. **Disaster Recovery**
```bash
# Restore from backup
./scripts/restore.sh /backups/codegenie/20240101
```

### High Availability

1. **Load Balancing**
```nginx
upstream codegenie {
    least_conn;
    server codegenie-1:8000;
    server codegenie-2:8000;
    server codegenie-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://codegenie;
    }
}
```

2. **Database Replication**
```yaml
database:
  primary:
    host: "postgres-primary"
    port: 5432
  replicas:
    - host: "postgres-replica-1"
      port: 5432
    - host: "postgres-replica-2"
      port: 5432
```

### Updates and Maintenance

1. **Zero-Downtime Updates**
```bash
# Rolling update
kubectl set image deployment/codegenie \
  codegenie=codegenie:v0.3.0 \
  --record

# Blue-green deployment
kubectl apply -f deploy/kubernetes/deployment-green.yaml
# Test green deployment
kubectl delete -f deploy/kubernetes/deployment-blue.yaml
```

2. **Maintenance Mode**
```bash
# Enable maintenance mode
codegenie maintenance enable

# Perform updates
./scripts/update.sh

# Disable maintenance mode
codegenie maintenance disable
```

## Troubleshooting Deployment

### Common Issues

1. **Out of Memory**
```bash
# Check memory usage
docker stats codegenie

# Increase memory limit
docker update --memory 16g codegenie
```

2. **Model Download Failures**
```bash
# Manual model download
docker exec -it codegenie ollama pull llama3.1:8b
```

3. **Connection Issues**
```bash
# Check Ollama service
docker exec -it codegenie curl http://localhost:11434/api/tags

# Check logs
docker logs codegenie
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Ollama health
curl http://localhost:11434/api/tags

# Database health
docker exec -it codegenie-postgres pg_isready
```

## Support

For deployment issues:
- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Visit [Community Forum](https://community.codegenie.dev)
- Email: support@codegenie.dev
