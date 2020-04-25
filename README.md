## Multi-Cloud-Explorer - VMware (Vsphere)

Inventory library for VMware (Vsphere Release)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build Status](https://travis-ci.org/multi-cloud-explorer/mce-lib-vsphere.svg)](https://travis-ci.org/multi-cloud-explorer/mce-lib-vsphere)
[![Coverage Status](https://coveralls.io/repos/github/multi-cloud-explorer/mce-lib-vsphere/badge.svg?branch=master)](https://coveralls.io/github/multi-cloud-explorer/mce-lib-vsphere?branch=master)
[![Code Health](https://landscape.io/github/multi-cloud-explorer/mce-lib-vsphere/master/landscape.svg?style=flat)](https://landscape.io/github/multi-cloud-explorer/mce-lib-vsphere/master)
[![Requirements Status](https://requires.io/github/multi-cloud-explorer/mce-lib-vsphere/requirements.svg?branch=master)](https://requires.io/github/multi-cloud-explorer/mce-lib-vsphere/requirements/?branch=master)

[Documentation](https://multi-cloud-explorer.readthedocs.org)

### Features

- [X] List all datacenters
- [X] List all clusters
- [X] List all datastores
- [X] List all virtual machines
- [ ] Command line client

### Installation

**Requires:**

- Python 3.7+
- Admin access to Vcenter

```bash
pip install git+https://github.com/multi-cloud-explorer/mce-lib-vpshere.git
```

### vCenter simulator

- https://github.com/vmware/govmomi/tree/master/vcsim

```bash
# Usage vcsim binary in mce-lib-vsphere
curl -L -o ~/bin/vcsim https://raw.githubusercontent.com/multi-cloud-explorer/mce-lib-vpshere/master/tests/utils/vcsim
chmod +x ~/bin/vcsim

# OR:

# Compile vcsim binary with Docker
docker run -it --rm -v ~/bin:/gopath/bin nimmis/golang go get -u github.com/vmware/govmomi/vcsim
sudo chown $USER:$USER ~/bin/vcsim

# Run simulator - 2 datacenters
~/bin/vcsim -api-version 6.5 -dc 2 -l 127.0.0.1:8989 -username user1 -password pass
```

### Usage

**Connect with URL:**

```shell
export MCE_VCENTER_URL=https://user1:pass@127.0.0.1:8989/sdk?timeout=120
```
```python
with Client() as cli:
    vm = cli.get_vm_by_name("DC0_H0_VM0")
    print(vm.name)
```

**Connect with host/port:**

```python
with Client(host="127.0.0.1", port=8989, username="user1", password="pass") as cli:
    vm = cli.get_vm_by_name("DC0_H0_VM0")
    print(vm.name)
```

**Display Vcenter Infos:**

```python
from pprint import pprint
from mce_lib_vsphere.core import Client

client = Client('https://user1:pass@127.0.0.1:8989/sdk')
client.connect()

si, content = client.connect()

pprint(client.vcenter_infos())
{
    'apiType': 'VirtualCenter',
    'apiVersion': '6.5',
    'build': '5973321',
    'licenseProductName': 'VMware VirtualCenter Server',
    'licenseProductVersion': '6.0',
    'osType': 'linux-amd64',
    'version': '6.5.0'
}

client.disconnect()
```

### TODO

- [ ] Publish to Pypi repository
- [ ] Sphinx doc
- [ ] Terraform templates
- [ ] Contrib doc

