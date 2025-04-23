# Python App ECS Deployment with GitHub Actions

This repository contains a Python Flask application that is deployed to Amazon ECS using GitHub Actions. The application includes a colorful homepage and health check endpoint.

## Project Overview

This project demonstrates how to:
- Create and deploy a simple Python Flask application
- Containerize the application using Docker
- Store the container image in Amazon ECR
- Deploy the application to Amazon ECS
- Set up a CI/CD pipeline using GitHub Actions

## Application Structure

```
python-app-demo/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container definition
└── templates/             # HTML templates
    ├── home.html          # Homepage template
    └── health.html        # Health check template
```

## Deployment Architecture

The application is deployed with the following AWS resources:
- Amazon ECR repository to store Docker images
- Amazon ECS cluster running in Fargate mode
- Amazon ECS Task Definition 
- Amazon ECS Service
- Application Load Balancer for routing traffic
- Target Group for health checks

## Prerequisites

- AWS CLI installed and configured
- Docker installed
- Access to GitHub for setting up GitHub Actions

## Deployment Steps

### 1. Create ECR Repository

```bash
aws ecr create-repository --repository-name python-app-demo --region your-aws-region
```

### 2. Build and Push Docker Image

```bash
# Build the Docker image
docker build -t python-app:latest .

# Tag the image with ECR repository URI
docker tag python-app:latest your-account-id.dkr.ecr.your-region.amazonaws.com/python-app-demo:latest

# Login to ECR
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com

# Push the image
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/python-app-demo:latest
```

### 3. Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name python-app-cluster
```

### 4. Create Task Definition

Create a `task-definition.json` file:

```json
{
  "family": "python-app-task",
  "networkMode": "awsvpc",
  "executionRoleArn": "arn:aws:iam::your-account-id:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "python-app",
      "image": "your-account-id.dkr.ecr.your-region.amazonaws.com/python-app-demo:latest",
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
          "awslogs-region": "your-region",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512"
}
```

Register the task definition:

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### 5. Create Target Group and Load Balancer

```bash
# Create a target group
aws elbv2 create-target-group \
  --name python-app-tg \
  --protocol HTTP \
  --port 5000 \
  --vpc-id your-vpc-id \
  --target-type ip \
  --health-check-path /health

# Create a load balancer
aws elbv2 create-load-balancer \
  --name python-app-alb \
  --subnets subnet-1 subnet-2 \
  --security-groups sg-id
```

### 6. Create ECS Service

```bash
aws ecs create-service \
  --cluster python-app-cluster \
  --service-name python-app-service \
  --task-definition python-app-task:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-1,subnet-2],securityGroups=[sg-id],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=target-group-arn,containerName=python-app,containerPort=5000"
```

### 7. Configure GitHub Secrets

In your GitHub repository, go to Settings > Secrets and Variables > Actions, and add these secrets:
* AWS_ACCESS_KEY_ID
* AWS_SECRET_ACCESS_KEY
* AWS_REGION
* ECR_REPOSITORY
* ECR_REGISTRY

## Accessing the Application

Access the application using the Load Balancer DNS name:

```
http://python-app-alb-xxxxxx.your-region.elb.amazonaws.com
```

The health check endpoint is available at:

```
http://python-app-alb-xxxxxx.your-region.elb.amazonaws.com/health
```

## Continuous Deployment with GitHub Actions

This repository includes a GitHub Actions workflow that automatically builds and deploys the application when changes are pushed to the main branch.

The workflow performs the following steps:
1. Checks out the code
2. Configures AWS credentials
3. Logs in to Amazon ECR
4. Builds and pushes the Docker image
5. Updates the ECS service to deploy the new image

## Local Development

To run the application locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at http://localhost:5000

## Troubleshooting

### Common Issues:

1. **Task fails to start**: Check the ECS task execution role permissions and CloudWatch logs.

2. **Health check failures**: Make sure the /health endpoint is correctly implemented and the security group allows traffic on port 5000.

3. **Image not found**: Verify that the image exists in ECR and the task definition has the correct image URI.

## License

Copyright (c) 2025 Joshua Oke