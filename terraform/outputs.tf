output "public_alb_dns_name" {
  description = "Public DNS name for the website."
  value       = aws_lb.public.dns_name
}

output "website_url" {
  description = "Open this URL after Nginx is installed and configured."
  value       = "http://${aws_lb.public.dns_name}/home"
}

output "internal_alb_dns_name" {
  description = "Private ALB DNS name for the webserver's Nginx API proxy."
  value       = aws_lb.internal.dns_name
}

output "webserver_public_ip" {
  description = "Public IP for administrator SSH to the webserver."
  value       = aws_instance.web.public_ip
}

output "applicationserver_public_ip" {
  description = "Public IP for administrator SSH to the applicationserver. Application traffic is still restricted to the internal ALB."
  value       = aws_instance.app.public_ip
}

output "rds_endpoint" {
  description = "RDS hostname (without port) for the Flask DB_HOST setting."
  value       = aws_db_instance.mysql.address
}

output "rds_port" {
  description = "RDS MySQL port."
  value       = aws_db_instance.mysql.port
}

output "rds_database_name" {
  description = "Initial MySQL database name."
  value       = aws_db_instance.mysql.db_name
}

output "rds_master_username" {
  description = "RDS master username selected in terraform.tfvars."
  value       = aws_db_instance.mysql.username
}
