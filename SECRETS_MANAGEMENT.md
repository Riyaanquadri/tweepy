# Secrets Management Guide

This document outlines how to securely manage credentials for the Crypto AI Twitter Bot in development and production.

## Development Environment

For local development, use the `.env` file with python-dotenv:

```bash
# Copy the example
cp .env.example .env

# Edit with your credentials
nano .env
```

**IMPORTANT**: Never commit `.env` to git. It's already in `.gitignore`.

## Production Deployment

### Option 1: AWS Secrets Manager (Recommended)

1. **Create secrets in AWS**:
```bash
aws secretsmanager create-secret \
  --name twitter-api-key \
  --secret-string '{"X_API_KEY":"your_key_here"}'
```

2. **Enable in environment**:
```bash
export USE_AWS_SECRETS=true
export AWS_REGION=us-east-1
```

3. **Set IAM permissions** on your EC2/Lambda/ECS role to allow `secretsmanager:GetSecretValue`

### Option 2: Google Cloud Secret Manager

```bash
gcloud secrets create X_API_KEY --replication-policy="automatic" \
  --data-file=- <<< "your_key_here"

# In your environment
export USE_GCP_SECRETS=true
export GCP_PROJECT_ID=your-project-id
```

### Option 3: HashiCorp Vault

```bash
vault kv put secret/twitter-bot \
  X_API_KEY=your_key \
  X_API_SECRET=your_secret
```

Set in environment:
```bash
export VAULT_ADDR=https://your-vault.example.com
export VAULT_TOKEN=your_token
export USE_VAULT=true
```

### Option 4: Docker Secrets (Swarm/Kubernetes)

```bash
# With Docker Compose
export X_API_KEY=your_key
docker-compose up -d
```

Secrets are injected at runtime via environment variables.

## Security Checklist

- ✅ `.env` file is in `.gitignore`
- ✅ No credentials in git history
- ✅ Use IAM roles instead of hardcoded credentials
- ✅ Rotate API keys regularly
- ✅ Enable MFA on provider accounts
- ✅ Monitor secret access logs
- ✅ Use short TTLs for temporary credentials
- ✅ Never share credentials in Slack/email
- ✅ Encrypt secrets in transit (HTTPS/TLS)
- ✅ Audit secret access

## Audit Trail

### AWS Secrets Manager
```bash
aws secretsmanager list-secret-version-ids --secret-id twitter-api-key
```

### Google Cloud
```bash
gcloud logging read "resource.type=secretmanager.googleapis.com"
```

### Vault
```bash
vault audit list
```

## Emergency Credential Rotation

If credentials are exposed:

1. **Revoke immediately**:
   - Twitter: Regenerate tokens in Developer Portal
   - OpenAI: Revoke key in API settings

2. **Update secrets store**:
   ```bash
   aws secretsmanager update-secret --secret-id X_ACCESS_TOKEN --secret-string "new_token"
   ```

3. **Restart bot** to pick up new credentials

4. **Monitor** for unauthorized activity

## Code Example

The bot automatically detects the configuration source:

```python
# In app/config.py
X_API_KEY = SecretsManager.get_secret('X_API_KEY')
# Checks in order:
# 1. Environment variable
# 2. .env file (dev)
# 3. AWS Secrets Manager (if USE_AWS_SECRETS=true)
# 4. Default value
```

## Troubleshooting

**Error: "Missing required secrets"**
- Check that all 6 keys are set in your secret store
- Verify IAM permissions for secret retrieval
- Check AWS region is correct

**Error: "boto3 not found"**
- For AWS: `pip install boto3`
- For GCP: `pip install google-cloud-secret-manager`

**Credentials not updating**
- The bot caches credentials at startup
- Restart the bot after updating secrets
- Check CloudWatch/Stackdriver logs
