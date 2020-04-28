resource "vsphere_folder" "inventory_folder" {
  path          = "${var.vm_folder}"
  type          = "vm"
  datacenter_id = "${data.vsphere_datacenter.datacenter.id}"
}

resource "vsphere_virtual_machine" "test-node" {
  count            = "${length(var.ips)}"
  name             = "${var.vm_name}-master-${count.index}"
  resource_pool_id = "${data.vsphere_resource_pool.pool.id}"
  datastore_id     = "${data.vsphere_datastore.datastore.id}"

  wait_for_guest_net_timeout = "-1"
  wait_for_guest_net_routable = false
  wait_for_guest_ip_timeout = "-1"

  num_cpus         = 2
  memory           = 8192
  folder           = "${vsphere_folder.inventory_folder.path}"

  network_interface {
    network_id   = "${data.vsphere_network.network.id}"
    adapter_type = "vmxnet3"
  }

  disk {
    label            = "${var.vm_name}-master-${count.index}-disk"
    size             = "20"
    thin_provisioned = true
    unit_number      = 0
  }
}
