# Zomato 3-tier AWS infrastructure

This Terraform configuration creates infrastructure only. It does not install or deploy the Zomato application.

```text
Internet → public ALB → webserver EC2 (Nginx, port 80)
                       → internal ALB (port 80)
                       → applicationserver EC2 (Flask, port 5000)
                       → private RDS MySQL (zomatodb, port 3306)
```

The branch's frontend makes API requests from the browser. For the requested private internal-ALB hop, the manual web deployment must set `API_BASE` to an empty string and configure Nginx to proxy `/api/` to the internal ALB. The exact post-apply deployment steps are below.

## Resources created

- One VPC, two public subnets, two private subnets, internet gateway, and public routes.
- Two Ubuntu 24.04 EC2 instances with public IPs for SSH and package installation. Security groups restrict application traffic to the ALB chain.
- Public and internal Application Load Balancers with HTTP listeners, target groups, and health checks.
- Private RDS MySQL 8.0 database named `zomatodb`, plus a final snapshot on Terraform destroy.
- Security groups that permit HTTP from the public ALB to Nginx, HTTP from Nginx to the internal ALB, TCP 5000 from the internal ALB to Flask, and MySQL 3306 from the app EC2 to RDS.

This uses one web EC2 and one app EC2, so it demonstrates the three tiers but does not provide EC2 redundancy. The two ALBs, EC2 instances, and RDS incur AWS charges while running.

## Before applying

1. Install Terraform and configure AWS credentials locally, for example with `aws configure` or an AWS CLI profile.
2. In AWS Console, create an EC2 key pair in `ap-south-1`, or choose one that already exists there.
3. Find your public IPv4 address. Use it as `YOUR_IP/32` for SSH access.
4. Copy `terraform.tfvars.example` to `terraform.tfvars`, then replace the key pair, SSH CIDR, and DB password values. `terraform.tfvars` is ignored by Git.
5. Keep the Terraform state file private. It contains the RDS password in plain text even though Terraform marks the variable sensitive.

Example PowerShell commands from this directory:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

Review the plan before approving `terraform apply`. Creating two ALBs and a database starts billable AWS resources.

## After apply: deploy the application manually

Get the resource values:

```powershell
terraform output
```

Use the `applicationserver_public_ip`, `webserver_public_ip`, `rds_endpoint`, `rds_database_name`, `rds_master_username`, `internal_alb_dns_name`, and `public_alb_dns_name` outputs below.

### 1. Deploy Flask on the applicationserver

SSH to `applicationserver_public_ip`, then run:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
cd /home/ubuntu
git clone --branch 3-tier-application https://github.com/bharatsairamkadali02/zomatoapp.git
cd /home/ubuntu/zomatoapp
python3 -m venv venv
source venv/bin/activate
python -m pip install -r application/requirements.txt
```

Edit `application/zomato-app.service`. Set `ALLOWED_ORIGIN` to `http://PUBLIC_ALB_DNS_NAME`, set a strong `SECRET_KEY`, and add these database settings using the values from Terraform outputs and the password in your local `terraform.tfvars`:

```ini
Environment="DB_HOST=RDS_ENDPOINT"
Environment="DB_PORT=3306"
Environment="DB_NAME=zomatodb"
Environment="DB_USER=zomato_admin"
Environment="DB_PASS=YOUR_RDS_PASSWORD"
Environment="USE_SQLITE=false"
```

Replace every example value. This branch's `run.py` initializes the schema and seed menu on startup; for that initialization, use the RDS master account created by Terraform. Keep the service file and password private.

Install and start the service:

```bash
sudo cp application/zomato-app.service /etc/systemd/system/zomato-app.service
sudo systemctl daemon-reload
sudo systemctl enable --now zomato-app
sudo systemctl status zomato-app
sudo journalctl -u zomato-app -n 50
```

The log should report a successful AWS RDS MySQL connection. If RDS is unreachable, this app can fall back to a local SQLite file; verify the log before proceeding.

### 2. Deploy Nginx on the webserver

SSH to `webserver_public_ip`, then clone the same branch and install Nginx:

```bash
sudo apt update
sudo apt install -y git nginx
cd /home/ubuntu
git clone --branch 3-tier-application https://github.com/bharatsairamkadali02/zomatoapp.git
```

Edit `/home/ubuntu/zomatoapp/web/config.js` and set:

```javascript
const API_BASE = '';
```

Edit `/home/ubuntu/zomatoapp/web/nginx.conf`. Inside the `server` block, add this location before the static `location /` block. Replace `INTERNAL_ALB_DNS_NAME` with the `internal_alb_dns_name` output:

```nginx
location /api/ {
    proxy_pass http://INTERNAL_ALB_DNS_NAME;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Then install and reload the site:

```bash
sudo cp /home/ubuntu/zomatoapp/web/nginx.conf /etc/nginx/sites-available/zomato
sudo ln -s /etc/nginx/sites-available/zomato /etc/nginx/sites-enabled/zomato
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl reload nginx
```

### 3. Verify the tiers

1. In **EC2 → Target Groups**, wait until `zomato-app-tg` and `zomato-web-tg` each show their instance as **Healthy**.
2. Open `http://PUBLIC_ALB_DNS_NAME/home` in a browser.
3. Sign up, log in, and place an order.
4. On the applicationserver, inspect `sudo journalctl -u zomato-app -f` and confirm the RDS connection message.

If a target is unhealthy, check the matching security-group source and port, the service status, and the health-check path. The app target checks `/api/restaurants` on port 5000; the web target checks `/home` on port 80.
