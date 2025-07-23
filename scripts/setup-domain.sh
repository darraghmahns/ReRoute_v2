#!/bin/bash
set -e

DOMAIN=${1}
EMAIL=${2:-admin@${1}}

if [ -z "$DOMAIN" ]; then
    echo "❌ Usage: ./setup-domain.sh <your-domain.com> [email@domain.com]"
    echo "Example: ./setup-domain.sh reroute.app admin@reroute.app"
    exit 1
fi

echo "🌐 Setting up SSL certificate for domain: $DOMAIN"

# Update nginx configuration with your domain
sed -i.bak "s/your-domain.com/$DOMAIN/g" nginx.conf
echo "✅ Updated nginx.conf with domain: $DOMAIN"

# Create SSL directory
mkdir -p ssl

# Generate SSL certificate with Let's Encrypt (Certbot)
if command -v certbot &> /dev/null; then
    echo "📜 Generating SSL certificate with Let's Encrypt..."
    
    # Stop nginx if running
    sudo systemctl stop nginx || true
    
    # Generate certificate
    sudo certbot certonly \
        --standalone \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d www.$DOMAIN
    
    # Copy certificates to project
    sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem
    sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/private.key
    sudo chown $USER:$USER ssl/cert.pem ssl/private.key
    
    echo "✅ SSL certificate generated and copied"
else
    echo "⚠️  Certbot not found. Installing certbot..."
    
    # Install certbot based on OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y certbot
        elif command -v yum &> /dev/null; then
            sudo yum install -y certbot
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install certbot
    fi
    
    echo "🔄 Please run this script again to generate the certificate"
    exit 1
fi

# Create renewal script
cat > scripts/renew-ssl.sh << EOF
#!/bin/bash
# SSL certificate renewal script
# Add to crontab: 0 2 * * 1 /path/to/renew-ssl.sh

certbot renew --quiet
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /path/to/project/ssl/cert.pem
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /path/to/project/ssl/private.key
docker-compose restart nginx
EOF

chmod +x scripts/renew-ssl.sh

echo "✅ Domain setup completed for: $DOMAIN"
echo ""
echo "📋 Next steps:"
echo "1. Point your domain's DNS A record to your server's IP address"
echo "2. Update your environment variables with the correct domain"
echo "3. Run your deployment script"
echo "4. Add SSL renewal to crontab: 0 2 * * 1 $(pwd)/scripts/renew-ssl.sh"
echo ""
echo "🔗 Your app will be available at: https://$DOMAIN"