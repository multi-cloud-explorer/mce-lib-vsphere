variable "vsphere_user" {
  type = "string"
}

variable "vsphere_password" {
  type = "string"
}

variable "vsphere_host" {
  type = "string"
}

variable "datacenter" {
  type = "string"
}

variable "cluster" {
  type = "string"
}

variable "datastore" {
  type = "string"
}

variable "network" {
  type = "string"
}

variable "vm_name" {
  type = "string"
}

variable "vm_folder" {
  type = "string"
}

variable "clustered_datastore" {
  type = "string"
}

variable "gateway" {
  type = "string"
}

variable "ips" {
  type = "list"
}

variable "subnet_mask" {
  default = ""
}
