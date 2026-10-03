variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Short prefix used in resource names and tags."
  type        = string
  default     = "zomato"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,15}$", var.project_name))
    error_message = "Use 2-16 lowercase letters, digits, or hyphens; start with a letter."
  }
}

variable "vpc_cidr" {
  description = "IPv4 CIDR block for the new VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "key_pair_name" {
  description = "Name of an existing EC2 key pair in the selected AWS region."
  type        = string
}

variable "ssh_ingress_cidr" {
  description = "Your public IPv4 address in CIDR format, for example 203.0.113.10/32."
  type        = string

  validation {
    condition     = can(cidrhost(var.ssh_ingress_cidr, 0))
    error_message = "Set ssh_ingress_cidr to a valid CIDR block. For one IP, use /32."
  }
}

variable "web_instance_type" {
  description = "EC2 instance type for the Nginx web server."
  type        = string
  default     = "t3.micro"
}

variable "app_instance_type" {
  description = "EC2 instance type for the Flask application server."
  type        = string
  default     = "t3.micro"
}

variable "db_name" {
  description = "Initial MySQL database name used by this application."
  type        = string
  default     = "zomatodb"
}

variable "db_master_username" {
  description = "RDS MySQL master username. Use it for this project deployment because run.py initializes the schema."
  type        = string
  default     = "zomato_admin"
}

variable "db_master_password" {
  description = "New RDS MySQL master password. Terraform stores this in its local state file; never commit the state."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_master_password) >= 8 && length(var.db_master_password) <= 41
    error_message = "Use an RDS-compatible password between 8 and 41 characters."
  }
}

variable "db_instance_class" {
  description = "RDS MySQL instance class. Confirm this class is available in the selected region/account."
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial RDS storage in GiB."
  type        = number
  default     = 20
}
