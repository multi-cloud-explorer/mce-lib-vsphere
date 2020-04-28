# Multi-Cloud-Explorer - VMware (Vsphere)

Inventory library for VMware (Vsphere Release)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build Status](https://travis-ci.org/multi-cloud-explorer/mce-lib-vsphere.svg)](https://travis-ci.org/multi-cloud-explorer/mce-lib-vsphere)
[![Coverage Status](https://coveralls.io/repos/github/multi-cloud-explorer/mce-lib-vsphere/badge.svg?branch=master)](https://coveralls.io/github/multi-cloud-explorer/mce-lib-vsphere?branch=master)
[![codecov](https://codecov.io/gh/multi-cloud-explorer/mce-lib-vsphere/branch/master/graph/badge.svg)](https://codecov.io/gh/multi-cloud-explorer/mce-lib-vsphere)
[![Code Health](https://landscape.io/github/multi-cloud-explorer/mce-lib-vsphere/master/landscape.svg?style=flat)](https://landscape.io/github/multi-cloud-explorer/mce-lib-vsphere/master)
[![Requirements Status](https://requires.io/github/multi-cloud-explorer/mce-lib-vsphere/requirements.svg?branch=master)](https://requires.io/github/multi-cloud-explorer/mce-lib-vsphere/requirements/?branch=master)
[![Documentation Status](https://readthedocs.org/projects/mce-lib-vpshere/badge/?version=latest&style=flat-square)](https://mce-lib-vpshere.readthedocs.org)

**Inventory library for VMware (Vsphere Release)**

### Features

- [X] List all Datacenter
- [X] List all Cluster
- [X] List all Datastores
- [X] List all Virtual Machines
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
### Pytest plugin

```python
# conftest.py
pytest_plugins = ['mce_lib_vsphere.pytest.plugin']

# test_yourtest.py

import pytest

from pyVmomi import vim

from mce_lib_vsphere import core

def test_get_all_vms(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_vms()
```

### TODO

- [ ] Publish to Pypi repository
- [ ] Sphinx doc
- [ ] Terraform templates ou Pulumi code for IAC
- [ ] Contrib doc

### Similar Python Projects

- [pyVirtualize](https://github.com/rocky1109/pyVirtualize)
- [vcdriver](https://github.com/Osirium/vcdriver)
- [py-vpoller](https://github.com/dnaeon/py-vpoller)
- [py-vconnector](https://github.com/dnaeon/py-vconnector)
- [ezmomi](https://github.com/snobear/ezmomi)
- [vcdriver](https://github.com/Lantero/vcdriver)
- [shortmomi](https://github.com/pschmitt/shortmomi)

