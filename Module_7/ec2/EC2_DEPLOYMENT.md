# EC2 Deployment Steps

## 1. Launch EC2 Instance

- AMI: Amazon Linux 2 (or Ubuntu 22.04)
- Instance type: t2.medium (or t3.medium)
- Security group rules:
  - SSH (22) from your IP
  - HTTP (8080) from anywhere (0.0.0.0/0)
  - RabbitMQ (15672) from your IP (optional)

## 2. Connect to EC2

```bash
ssh -i your-key.pem ec2-user@<public-ip>