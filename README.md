# pyAppEcsGithubActions# Python App to AWS ECS with GitHub Actions

This project demonstrates a complete CI/CD pipeline for deploying a Python application to AWS ECS using GitHub Actions.

## Project Structure

```
python-app-ecs/
├── app/
│   ├── __init__.py
│   └── app.py               # Main Flask application
├── .github/
│   └── workflows/
│       └── deploy.yml       # GitHub Actions workflow
├── Dockerfile               # Container configuration
├── requirements.txt         # Python dependencies
├── task-definition.json     # ECS task definition
├── scripts/
│   ├── create_ecr.sh        # Script to create ECR repository
│   ├── create_ecs_cluster.sh # Script to create ECS cluster
│   ├── create_load_balancer.sh # Script to create ALB
│   └── create_service.sh    # Script to create ECS service
└── README.md                # Project documentation
```

## File Contents

### app/app.py
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Python app is running!"})

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Welcome to my AWS ECS Deployed Python App!",
        "status": "running",
        "version": "1.0.0"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### app/__init__.py
```python
# Empty init file to make the directory a package
```

### requirements.txt
```
flask==2.3.3
gunicorn==21.2.0
```

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.app:app"]
```

### .github/workflows/deploy.yml
```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ secrets.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: ${{ secrets.ECR_REPOSITORY }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        echo "::set-output name=image::$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"
        
    - name: Update ECS service
      run: |
        aws ecs update-service --cluster ${{ secrets.ECS_CLUSTER }} \
                               --service ${{ secrets.ECS_SERVICE }} \
                               --force-new-deployment
```

### task-definition.json
```json
{
  "family": "python-app-task",
  "networkMode": "awsvpc",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "python-app",
      "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/python-app-demo:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 5000,
          "hostPort": 5000,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/python-app",
          "awslogs-region": "REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512"
}
```

### scripts/create_ecr.sh
```bash
#!/bin/bash
# Create an ECR repository for the Python application

# Set your AWS region
REGION="YOUR_REGION"
REPO_NAME="python-app-demo"

# Create the ECR repository
echo "Creating ECR repository: $REPO_NAME"
aws ecr create-repository \
    --repository-name $REPO_NAME \
    --region $REGION

echo "ECR repository created."
echo "Repository URI: $(aws ecr describe-repositories --repository-names $REPO_NAME --query 'repositories[0].repositoryUri' --output text)"
```

### scripts/create_ecs_cluster.sh
```bash
#!/bin/bash
# Create an ECS cluster for the Python application

# Set your AWS region
REGION="YOUR_REGION"
CLUSTER_NAME="python-app-cluster"

# Create the ECS cluster
echo "Creating ECS cluster: $CLUSTER_NAME"
aws ecs create-cluster \
    --cluster-name $CLUSTER_NAME \
    --region $REGION

echo "ECS cluster created."
```

### scripts/create_load_balancer.sh
```bash
#!/bin/bash
# Create an Application Load Balancer for the Python application

# Set your AWS region and resource names
REGION="YOUR_REGION"
ALB_NAME="python-app-alb"
TG_NAME="python-app-tg"

# You must replace these values with your actual VPC, subnet and security group IDs
VPC_ID="vpc-xxxxxxxx"
SUBNET_1="subnet-xxxxxxxx"
SUBNET_2="subnet-yyyyyyyy"
SECURITY_GROUP="sg-zzzzzzzz"

# Create a target group
echo "Creating target group: $TG_NAME"
TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
    --name $TG_NAME \
    --protocol HTTP \
    --port 5000 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-path /health \
    --region $REGION \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

echo "Target group created: $TARGET_GROUP_ARN"

# Create a load balancer
echo "Creating ALB: $ALB_NAME"
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name $ALB_NAME \
    --subnets $SUBNET_1 $SUBNET_2 \
    --security-groups $SECURITY_GROUP \
    --region $REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

echo "ALB created: $ALB_ARN"

# Create a listener
echo "Creating listener"
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
    --region $REGION

echo "Load balancer setup complete."
echo "ALB DNS Name: $(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --query 'LoadBalancers[0].DNSName' --output text)"
```

### scripts/create_service.sh
```bash
#!/bin/bash
# Create an ECS service for the Python application

# Set your AWS region and resource names
REGION="YOUR_REGION"
CLUSTER_NAME="python-app-cluster"
SERVICE_NAME="python-app-service"
TASK_DEFINITION="python-app-task"
SECURITY_GROUP="sg-zzzzzzzz"
SUBNET_1="subnet-xxxxxxxx"
SUBNET_2="subnet-yyyyyyyy"
TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:REGION:ACCOUNT_ID:targetgroup/python-app-tg/xxxxxxxx"

# Create the ECS service
echo "Creating ECS service: $SERVICE_NAME"
aws ecs create-service \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --task-definition $TASK_DEFINITION \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=python-app,containerPort=5000" \
    --region $REGION

echo "ECS service created."
```

### README.md
```markdown
# Python App to AWS ECS with GitHub Actions

This project demonstrates how to deploy a Python Flask application to AWS ECS using GitHub Actions for CI/CD.

## Project Overview

- Simple Python Flask application with health check endpoint
- Dockerized application
- AWS ECR for container registry
- AWS ECS (Fargate) for container orchestration
- Application Load Balancer for public access
- GitHub Actions for CI/CD pipeline

## Prerequisites

- AWS Account
- GitHub Account
- AWS CLI installed and configured
- Docker installed locally (for testing)

## Setup Instructions

1. Fork/clone this repository
2. Create the AWS resources:
   - Run the scripts in the `scripts/` directory to create the necessary AWS resources
   - Alternatively, use the AWS Console to create these resources
3. Add the required secrets to your GitHub repository:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_REGION
   - ECR_REPOSITORY
   - ECS_CLUSTER
   - ECS_SERVICE
4. Push to your main branch to trigger the deployment

## Local Testing

To test the application locally:

```bash
# Build the Docker image
docker build -t python-app:local .

# Run the container
docker run -p 5000:5000 python-app:local

# Test the API
curl http://localhost:5000/health
```

## Architecture

This project uses AWS Fargate, which is a serverless compute engine for containers. The architecture includes:

- GitHub Actions for CI/CD
- ECR for storing Docker images
- ECS with Fargate for running containers
- Application Load Balancer for routing traffic
- IAM roles for security

## Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/index.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Flask Documentation](https://flask.palletsprojects.com/)
```