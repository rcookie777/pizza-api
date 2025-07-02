#!/bin/bash

# Setup API subdomain with HTTPS for Pizza Index API
# This script sets up Nginx with Let's Encrypt SSL certificates for api.monitorthesituation.lol

echo "Setting up API subdomain with HTTPS..."

# Update system
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx configuration for API subdomain
sudo tee /etc/nginx/sites-available/api.monitorthesituation.lol << 'EOF'
server {
    listen 80;
    server_name api.monitorthesituation.lol;
    
    # CORS headers for frontend
    add_header 'Access-Control-Allow-Origin' 'https://monitorthesituation.lol' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
    add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;

    # Handle preflight requests
    if ($request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' 'https://monitorthesituation.lol' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain; charset=utf-8';
        add_header 'Content-Length' 0;
        return 204;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/api.monitorthesituation.lol /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "Nginx configured for api.monitorthesituation.lol"
echo ""
echo "Next steps:"
echo "1. Make sure your DNS has an A record: api.monitorthesituation.lol -> 64.181.223.22"
echo "2. Wait a few minutes for DNS to propagate"
echo "3. Run: sudo certbot --nginx -d api.monitorthesituation.lol"
echo "4. Deploy your frontend to Cloudflare Pages"
echo "5. Set VITE_API_URL = 'https://api.monitorthesituation.lol' in Cloudflare Pages environment variables" 