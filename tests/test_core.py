from pprint import pprint

from freezegun import freeze_time
import pytest

from mce_lib_vsphere import core

def test_parse_url():

    client = core.Client(host='127.0.0.1')

    assert client.host == "127.0.0.1"
    assert client.port == 443
    assert client.path == "/sdk"
    assert client.timeout == core.VCENTER_TIMEOUT
    assert client.pool_size == 5
    assert client.username is None
    assert client.password is None
    assert client.is_ssl is True
    assert client.verify is True
    assert client.debug is False

    host = "https://usertest:passtest@127.0.0.1:8900/sdk2?timeout=1&pool_size=10&verify=False&debug=1"
    client = core.Client(host)

    assert client.host == "127.0.0.1"
    assert client.port == 8900
    assert client.path == "/sdk2"
    assert client.timeout == 1
    assert client.pool_size == 10
    assert client.username == "usertest"
    assert client.password == "passtest"
    assert client.is_ssl is True
    assert client.verify is False
    assert client.debug is True

    host = "http://127.0.0.1"
    client = core.Client(host)

    assert client.is_ssl is False

def test_connect(vsphere_server):
    url = vsphere_server

    client = core.Client(host=url)
    assert client.is_ssl is True
    client.connect()
    assert client.is_connected is  True
    assert len(client.get_all_datacenters()) == 2
    client.disconnect()

    with core.Client(host=url) as client:
        client.connect()
        assert len(client.get_all_datacenters()) > 0

@pytest.mark.skip("TODO")
def reuse_session():
    # TODO: test connect autre instance avec le meme token
    pass

@pytest.mark.skip("TODO")
def test_get_all(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.skip("TODO")
def test_dump_to_dict(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

def test_vcenter_infos(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        data = client.vcenter_infos()

        assert data == {
            'apiType': 'VirtualCenter',
             'apiVersion': vcsim_settings['api_version'],
             'build': '5973321',
             'licenseProductName': 'VMware VirtualCenter Server',
             'licenseProductVersion': '6.0',
             'osType': 'linux-amd64',
             'version': '6.5.0'
        }

# FIXME: @freeze_time("2019-01-01")
@pytest.mark.skip("TODO")
def test_get_current_session(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        data = client.get_current_session()
        #pprint(data)
        assert data == {
            'callCount': 4,
            'fullName': vcsim_settings["username"],
            'ipAddress': '127.0.0.1',
            'locale': 'en_US',
            'loginTime': "", # https://github.com/vmware/pyvmomi/blob/master/tests/test_iso8601.py#L62
            'userAgent': 'pyvmomi Python/3.7.6 (Linux; 5.3.16-300.fc31.x86_64; x86_64)',
            'userName': vcsim_settings["username"]
        }

def test_get_all_folders(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_folders()
        assert len(objects) > 0
        data = client.dump_to_dict(objects[0])

def test_get_all_hosts(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_hosts()

        assert len(objects) > 0
        data = client.dump_to_dict(objects[0])

def test_get_all_pools(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_pools()

        assert len(objects) > 0
        data = client.dump_to_dict(objects[0])

def test_get_all_clusters(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_clusters()

        assert len(objects) > 0
        data = client.dump_to_dict(objects[0])

def test_get_all_datacenters(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_datacenters()

        assert len(objects) > 0
        data = client.dump_to_dict(objects[0])

def test_get_all_datastores(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_datastores()

        assert len(objects) > 0
        data = client.dump_to_dict(objects[0])

def test_get_all_vms(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_vms()

        assert len(objects) > 0
        data = client.dump_to_dict(objects[0])

def test_get_all_dvswitches(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_dvswitches()

        assert len(objects) > 0
        data = client.dump_to_dict(objects[0])

def test_get_all_dport_groups(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_dport_groups()

        assert len(objects) > 0
        data = client.dump_to_dict(objects[0])

def test_get_cluster_infos(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_clusters()

        data = client.get_cluster_infos(objects[0])
        #pprint(data)
        assert data == {
            'effectiveCpu': 6882,
            'effectiveMemory': 12883292160,
            'name': 'DC0_C0',
            'numCpuCores': 6,
            'numCpuThreads': 6,
            'numEffectiveHosts': 3,
            'numHosts': 3,
            'totalCpu': 6882,
            'totalMemory': 12883292160
        }

        """
        {
            "name": cluster.name,
            "totalCpu": cluster.summary.totalCpu,
            "numCpuCores": cluster.summary.numCpuCores,
            "totalMemory": cluster.summary.totalMemory,
            "numCpuThreads": cluster.summary.numCpuThreads,
            "effectiveCpu": cluster.summary.effectiveCpu,
            "effectiveMemory": cluster.summary.effectiveMemory,
            "numHosts": cluster.summary.numHosts,
            "numEffectiveHosts": cluster.summary.numEffectiveHosts,
        }        
        """


def test_get_hosts_in_datacenter(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_datacenters()

        hosts = client.get_hosts_in_datacenter(objects[0])
        assert len(hosts) > 0


def test_get_vms_in_datacenter(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_datacenters()

        vms = client.get_vms_in_datacenter(objects[0])
        assert len(vms) > 0

def test_get_host_infos(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_hosts()

        data = client.get_host_infos(objects[0])
        #pprint(data)
        assert data == {
            'apiVersion': '6.5',
            'fullName': 'VMware ESXi 6.5.0 build-5969303',
            'managementServerIp': None,
            'name': 'DC0_H0',
            'version': '6.5.0'
        }

def test_get_pool_infos(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_pools()

        data = client.get_pool_infos(objects[0])
        #pprint(data)
        assert data == {
            "name": "Resources"
        }

def test_get_datastore_infos(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_datastores()

        data = client.get_datastore_infos(objects[0])
        #pprint(data)
        # TODO: voir présivilité
        del data['id']
        assert data == {
            'accessible': True,
            'capacity': 3117400064,
            'freespace': 3083849728,
            #'id': '/tmp/govcsim-DC0-LocalDS_0-764558186@folder-5',
            'maintenance_mode': 'normal',
            'name': 'LocalDS_0',
            'provisioned': 33550336,
            'type': 'OTHER',
            'uncommitted': 0
        }


@pytest.mark.skip("TODO")
def test_get_vm_by_name(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.skip("TODO")
def test_getNICs(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

# FIXME: @freeze_time("2019-01-01")
def test__get_vm_infos(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_vms()

        data = client._get_vm_infos(objects[0])
        #pprint(data)
        del data['boot_time'] # FIXME
        assert data == {
            'annotation': '',
            'cpu': 1,
            'diskGB': 0.0,
            'fields': {},
            'guestFamily': 'linuxGuest',
            'guestOperationsReady': None,
            'guestState': '',
            'guestStateChangeSupported': None,
            'hostname': None,
            'interactiveGuestOperationsReady': None,
            'is_template': False,
            'mem': 0.03125,
            'name': 'DC0_H0_VM0',
            'net': {},
            'ostype': 'otherGuest',
            'path': '[LocalDS_0] DC0_H0_VM0/DC0_H0_VM0.vmx',
            'state': 'poweredOn',
            'toolsRunningStatus': 'guestToolsNotRunning',
            'toolsStatus': 'toolsNotInstalled',
            'toolsVersion': '0'
        }

# FIXME: @freeze_time("2019-01-01")
def test_get_vm_infos(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_vms()

        data = client.get_vm_infos(objects[0])
        #pprint(data)

        del data['vm']['boot_time'] # FIXME
        del data['properties'] # TODO: properties
        assert data == {
            "vm": {
                'annotation': '',
                'cpu': 1,
                'diskGB': 0.0,
                'fields': {},
                'guestFamily': 'linuxGuest',
                'guestOperationsReady': None,
                'guestState': '',
                'guestStateChangeSupported': None,
                'hostname': None,
                'interactiveGuestOperationsReady': None,
                'is_template': False,
                'mem': 0.03125,
                'name': 'DC0_H0_VM0',
                'net': {},
                'ostype': 'otherGuest',
                'path': '[LocalDS_0] DC0_H0_VM0/DC0_H0_VM0.vmx',
                'state': 'poweredOn',
                'toolsRunningStatus': 'guestToolsNotRunning',
                'toolsStatus': 'toolsNotInstalled',
                'toolsVersion': '0'
            },
        }

@pytest.mark.skip("TODO")
def test_get_custom_fields(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.skip("TODO")
def test_get_object_by_name(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.skip("TODO")
def test_is_valid_run_tools(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.skip("TODO")
def test_is_valid_tools(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.skip("TODO")
def test_is_power_on(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.skip("TODO")
def test_is_vm_ready(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.skip("TODO")
def test_get_vm_roles(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

def test_resource_id(vsphere_server):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        dc = client.get_all_datacenters()[0]
        resource_id = client.resource_id(dc)
        assert resource_id == 'group-d1/datacenter-2'
