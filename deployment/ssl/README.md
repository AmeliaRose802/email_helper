# SSL Certificates Directory

This directory should contain SSL/TLS certificates for HTTPS support.

## For Development

Use self-signed certificates or Let's Encrypt staging:

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

## For Production

Use Let's Encrypt or certificates from your certificate authority:

### Let's Encrypt with cert-manager (Kubernetes)

The Kubernetes ingress configuration includes cert-manager annotations for automatic SSL certificate provisioning.

### Manual Certificate Placement

1. Place your certificate files in this directory:
   - `cert.pem` - SSL certificate
   - `key.pem` - Private key
   - `chain.pem` - Certificate chain (if applicable)

2. Update nginx.conf with correct paths:
   ```nginx
   ssl_certificate /etc/nginx/ssl/cert.pem;
   ssl_certificate_key /etc/nginx/ssl/key.pem;
   ```

3. Restart nginx:
   ```bash
   docker-compose restart nginx
   ```

## Security Notes

- **NEVER commit SSL private keys to version control**
- Store certificates securely (e.g., using secrets management)
- Rotate certificates before expiration
- Use strong cipher suites
- Enable HSTS (HTTP Strict Transport Security)

## Certificate Renewal

Set up automatic renewal with Let's Encrypt or your CA's renewal process.
