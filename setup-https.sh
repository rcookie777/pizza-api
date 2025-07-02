#!/bin/bash

# Setup HTTPS for Pizza Index API on Oracle Cloud
# This script sets up Nginx with Let's Encrypt SSL certificates

echo "Setting up HTTPS for Pizza Index API..."

# Update system
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/pizza-api << EOF
server {
    listen 80;
    server_name 64.181.223.22;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/pizza-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "Nginx configured. Now you need to:"
echo "1. Get a domain name pointing to 64.181.223.22"
echo "2. Run: sudo certbot --nginx -d your-domain.com"
echo "3. Update VITE_API_URL in Cloudflare Pages to: https://your-domain.com" 