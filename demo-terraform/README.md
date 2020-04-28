# Vcenter Simulator and Terraform template for testing library

**Install requirements:**

* [vcsim](https://github.com/vmware/govmomi/tree/master/vcsim)
* [govc](https://github.com/vmware/govmomi/tree/master/govc)
* [terraform](https://www.terraform.io/docs/providers/vsphere/)

**1. vCenter Simulator Install**

- https://github.com/vmware/govmomi/tree/master/vcsim

```shell
# Usage vcsim binary in mce-lib-vsphere
curl -L -o ~/bin/vcsim https://raw.githubusercontent.com/multi-cloud-explorer/mce-lib-vpshere/master/utils/vcsim
chmod +x ~/bin/vcsim

# OR:

# Compile vcsim binary with Docker
docker run -it --rm -v ~/bin:/gopath/bin nimmis/golang go get -u github.com/vmware/govmomi/vcsim
sudo chown $USER:$USER ~/bin/vcsim

# Run simulator - 2 datacenters
~/bin/vcsim -api-version 6.5 -dc 2 -l 127.0.0.1:8989 -username user1 -password pass
```

**2. Clone this repository:**

```shell script
git clone https://github.com/multi-cloud-explorer/mce-lib-vpshere.git
cd mce-lib-vpshere
```

**3. Launch Vcenter Simulator:**

```shell script
./utils/vcsim -api-version 6.5 \
  -l 0.0.0.0:8989 \
  -username user1 -password pass \
   -app 0 -vm 0
```

*Copie export line from vcsim console:*"
export GOVC_INSECURE=true GOVC_URL=https://user1:pass@10.0.2.15:8989/sdk GOVC_SIM_PID=2800308

> **Open a new windows**

**4. Terraform Install**

```shell script
curl -L -O https://releases.hashicorp.com/terraform/0.12.24/terraform_0.12.24_linux_amd64.zip
unzip terraform_0.12.24_linux_amd64.zip -d .
sudo mv terraform /usr/local/bin
terraform --version
rm -f terraform_0.12.24_linux_amd64.zip
```

**5. Test with govc command before terraform:**

```shell
govc find -l
```

*Output:*
```
Folder                       /
Datacenter                   /DC0
Folder                       /DC0/vm
Folder                       /DC0/host
ComputeResource              /DC0/host/DC0_H0
HostSystem                   /DC0/host/DC0_H0/DC0_H0
ResourcePool                 /DC0/host/DC0_H0/Resources
ClusterComputeResource       /DC0/host/DC0_C0
HostSystem                   /DC0/host/DC0_C0/DC0_C0_H0
HostSystem                   /DC0/host/DC0_C0/DC0_C0_H1
HostSystem                   /DC0/host/DC0_C0/DC0_C0_H2
ResourcePool                 /DC0/host/DC0_C0/Resources
Folder                       /DC0/datastore
Datastore                    /DC0/datastore/LocalDS_0
Folder                       /DC0/network
Network                      /DC0/network/VM Network
DistributedVirtualSwitch     /DC0/network/DVS0
DistributedVirtualPortgroup  /DC0/network/DVS0-DVUplinks-9
DistributedVirtualPortgroup  /DC0/network/DC0_DVPG0
```

**6. Create VM Template with govc:**

```shell
govc vm.create -m 2048 -c 2 -g windows9Server64Guest -net.adapter vmxnet3 \
   -disk.controller pvscsi -ds=datastore/LocalDS_0 -pool=DC0_H0/Resources \
   -net="network/VM Network" template-vm
```

**7. Run terraform:**

```shell
cd demo-terraform
terraform init
terraform plan
terraform apply -auto-approve
```

**8. Test with govc command after terraform:**

```shell
govc find -l
```

> Diff only:

```
VirtualMachine               /DC0/vm/template-vm
Folder                       /DC0/vm/vcsim-test-folder
VirtualMachine               /DC0/vm/vcsim-test-folder/vcsim-test-master-0
VirtualMachine               /DC0/vm/vcsim-test-folder/vcsim-test-master-1
```
