from pprint import pprint

from freezegun import freeze_time
import pytest
from pyVmomi import vim
from furl import furl

from mce_lib_vsphere import core
from mce_lib_vsphere import exceptions

def test_parse_url():

    client = core.Client(host='127.0.0.1')

    assert client.host == "127.0.0.1"
    assert client.port == 443
    assert client.path == "/sdk"
    assert client.timeout == 60
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

    # TODO: test bad url

def test_connect(vsphere_server):
    url = vsphere_server

    # TODO: test with environ varialble for URL

    client = core.Client(host=url)
    assert client.is_ssl is True

    client.connect()
    assert client.is_connected is  True

    assert len(client.get_all_datacenters()) == 2
    client.disconnect()

    with core.Client(host=url) as client:
        client.connect()
        assert len(client.get_all_datacenters()) > 0

def test_timeout_connect():

    client = core.Client(host="127.0.0.2", username="user", password="pass", timeout=2)

    msg = "Connection could not be established for host [127.0.0.2:443] with timeout [2]"

    with pytest.raises(exceptions.ConnectionError) as excinfo:
        client.connect()
    assert str(excinfo.value) == msg

def test_authentication_error(vsphere_server):
    url = vsphere_server
    url = furl(url)

    client = core.Client(host=url.host, port=url.port, username=url.username, password="badpass")

    with pytest.raises(exceptions.AuthenticationError) as excinfo:
        client.connect()
    assert str(excinfo.value) == "invalid authentication for [user1]"

    client = core.Client(host=url.host, port=url.port, username="BADUSER", password="badpass")

    with pytest.raises(exceptions.AuthenticationError) as excinfo:
        client.connect()
    assert str(excinfo.value) == "invalid authentication for [BADUSER]"

    # TODO: FatalError

@pytest.mark.mce_todo
def reuse_session():
    # TODO: test connect autre instance avec le meme token
    pass
    # from mce_lib_vsphere.core import Client
    # client = Client('https://user:pass@127.0.0.1:8989/sdk')
    # si, content = client.connect()
    # stub = si._stub
    #
    # soapStub = SoapStubAdapter(host="127.0.0.1", port=8989)
    # si2 = vim.ServiceInstance("ServiceInstance",soapStub)
    # sessionCookie = stub.cookie
    # httpContext = VmomiSupport.GetHttpContext()
    # cookie = cookies.SimpleCookie()
    # cookie["vmware_soap_session"] = sessionCookie
    # httpContext["cookies"] = cookie
    # VmomiSupport.GetRequestContext()["vcSessionCookie"] = sessionCookie
    # hostname = stub.host.split(":")[0]
    # port = int(stub.host.split(":")[1])
    # context = None
    # if hasattr(ssl, "_create_unverified_context"):
    #     context = ssl._create_unverified_context()
    # stub2 = pyVmomi.SoapStubAdapter(host=hostname, port=port, sslContext=context)
    # si2 = vim.ServiceInstance("ServiceInstance", stub2)
    # content = si2.RetrieveContent()
    # content.about


@pytest.mark.mce_todo
def test_get_all(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.mce_todo
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

#@freeze_time("2019-01-01", tz_offset=-4)
def test_get_current_session(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        data = client.get_current_session()
        pprint(data)
        del data['loginTime'] # FIXME: bug avec freeze_time
        del data['callCount']
        del data['userAgent']
        assert data == {
            #'callCount': 4,
            'fullName': vcsim_settings["username"],
            'ipAddress': '127.0.0.1',
            'locale': 'en_US',
            #'loginTime': "", # https://github.com/vmware/pyvmomi/blob/master/tests/test_iso8601.py#L62
            #'userAgent': 'pyvmomi Python/3.7.6 (Linux; 5.3.16-300.fc31.x86_64; x86_64)',
            'userName': vcsim_settings["username"]
        }

def test_get_all_folders(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_folders()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.Folder) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2/folder-3'

        data = client.dump_to_dict(objects[0])

def test_get_all_hosts(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_hosts()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.HostSystem) is True

        #for host in objects:
        #    print(client.resource_id(host))

        resource_id = client.resource_id(objects[0])
        #FIXME: assert resource_id == 'group-d1/datacenter-2/folder-4/clustercomputeresource-30/host-37'

        data = client.dump_to_dict(objects[0])

def test_get_all_pools(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_pools()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.ResourcePool) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2/folder-4/computeresource-26/resgroup-25'

        data = client.dump_to_dict(objects[0])


def test_get_all_clusters(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_clusters()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.ClusterComputeResource) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2/folder-4/clustercomputeresource-30'

        data = client.dump_to_dict(objects[0])

def test_get_all_datacenters(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_datacenters()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.Datacenter) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2'

        data = client.dump_to_dict(objects[0])

def test_get_all_datastores(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_datastores()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.Datastore) is True

        resource_id = client.resource_id(objects[0])
        # FIXME: 
        #assert resource_id == 'group-d1/datacenter-2/folder-5//tmp/govcsim-dc0-localds_0-150284432@folder-5'

        data = client.dump_to_dict(objects[0])

def test_get_all_vms(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_vms()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.VirtualMachine) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2/folder-3/vm-231'

        data = client.dump_to_dict(objects[0])

def test_get_all_dvswitches(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_dvswitches()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.DistributedVirtualSwitch) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2/folder-6/dvs-11'

        data = client.dump_to_dict(objects[0])

def test_get_all_dport_groups(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_dport_groups()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.dvs.DistributedVirtualPortgroup) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2/folder-6/dvportgroup-13'

        data = client.dump_to_dict(objects[0])

def test_get_all_virtualapps(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_virtualapps()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.VirtualApp) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2/folder-4/clustercomputeresource-30/resgroup-29/virtualapp-56'

        # FIXME: data = client.dump_to_dict(objects[0])

def test_get_all_networks(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_networks()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.Network) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2/folder-6/network-7'

        data = client.dump_to_dict(objects[0])

def test_get_all_opaque_networks(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_opaque_networks()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.OpaqueNetwork) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2/folder-6/opaquenetwork-16'

        data = client.dump_to_dict(objects[0])

def test_get_all_compute_resources(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_compute_resources()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.ComputeResource) is True

        resource_id = client.resource_id(objects[0])
        assert resource_id == 'group-d1/datacenter-2/folder-4/computeresource-26'

        data = client.dump_to_dict(objects[0])

def test_get_all_storage_pods(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_storage_pods()

        assert len(objects) > 0

        assert isinstance(objects[0], vim.StoragePod) is True

        resource_id = client.resource_id(objects[0])

        data = client.dump_to_dict(objects[0])

@pytest.mark.skip("FIXME data values")
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

@pytest.mark.skip("FIXME data values")
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


def test_search_vm_by_uuid(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_vms()

        vm = objects[0]
        resource_id = client.resource_id(vm)

        instance_uuid = vm.summary.config.instanceUuid
        vm_found = client.search_vm_by_uuid(instance_uuid)
        assert vm_found is not None
        assert resource_id == client.resource_id(vm_found)

        bios_uuid = vm.summary.config.uuid
        vm_found = client.search_vm_by_uuid(bios_uuid, False)
        assert vm_found is not None
        assert resource_id == client.resource_id(vm_found)

        vm_not_found = client.search_vm_by_uuid("baduuid")
        assert vm_not_found is None

def test_get_vm_by_name(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_vms()

        # vm found success
        vm = client.get_vm_by_name(objects[0].name)
        assert vm is not None

        # vm not found without Exception
        vm = client.get_vm_by_name("BADNAME")
        assert vm is None

        # vm not found with VmNotFoundError Exception
        msg = f"vm [BADNAME] not found in vcenter [{client.host}:{client.port}] for username [{client.username}]"
        with pytest.raises(exceptions.VmNotFoundError) as excinfo:
            vm = client.get_vm_by_name("BADNAME", raise_error=True)
        assert str(excinfo.value) == msg


@pytest.mark.mce_todo
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
        del data['mem_mb'] # FIXME

        assert data == {
            'annotation': '',
            'bios_uuid': '265104de-1472-547c-b873-6dc7883fb6cb',
            #'boot_time': '2020-04-26T20:55:35.8409+02:00',
            'cpu_cores': 1,
            'cpu_count': 1,
            'create_date': None,
            'diskGB': 0.0,
            'fields': {},
            'guestFamily': 'linuxGuest',
            'guestOperationsReady': None,
            'guestState': '',
            'guestStateChangeSupported': None,
            'hostname': None,
            'interactiveGuestOperationsReady': None,
            'is_template': False,
            #'mem_mb': 32,
            'name': 'DC0_H0_VM0',
            'net': {},
            'ostype': 'otherGuest',
            'state': 'poweredOn',
            'toolsRunningStatus': 'guestToolsNotRunning',
            'toolsStatus': 'toolsNotInstalled',
            'toolsVersion': '0',
            'uuid': 'b4689bed-97f0-5bcd-8a4c-07477cc8f06f',
            'vm_path_name': '[LocalDS_0] DC0_H0_VM0/DC0_H0_VM0.vmx'
        }

# FIXME: @freeze_time("2019-01-01")
def test_get_vm_infos(vsphere_server, vcsim_settings):
    url = vsphere_server

    # FIXME: A faire sur un template

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_vms()

        data = client.get_vm_infos(objects[0])
        #pprint(data)

        del data['vm']['boot_time'] # FIXME
        del data['vm']['mem_mb'] # FIXME
        del data['properties'] # TODO: properties

        assert data == {
            "vm": {
                'annotation': '',
                'bios_uuid': '265104de-1472-547c-b873-6dc7883fb6cb',
                # 'boot_time': '2020-04-26T20:55:35.8409+02:00',
                'cpu_cores': 1,
                'cpu_count': 1,
                'create_date': None,
                'diskGB': 0.0,
                'fields': {},
                'guestFamily': 'linuxGuest',
                'guestOperationsReady': None,
                'guestState': '',
                'guestStateChangeSupported': None,
                'hostname': None,
                'interactiveGuestOperationsReady': None,
                'is_template': False,
                # 'mem_mb': 32,
                'name': 'DC0_H0_VM0',
                'net': {},
                'ostype': 'otherGuest',
                'state': 'poweredOn',
                'toolsRunningStatus': 'guestToolsNotRunning',
                'toolsStatus': 'toolsNotInstalled',
                'toolsVersion': '0',
                'uuid': 'b4689bed-97f0-5bcd-8a4c-07477cc8f06f',
                'vm_path_name': '[LocalDS_0] DC0_H0_VM0/DC0_H0_VM0.vmx'
            },
        }

@pytest.mark.mce_todo
def test_get_custom_fields(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.mce_todo
def test_get_object_by_name(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.mce_todo
def test_is_valid_run_tools(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.mce_todo
def test_is_valid_tools(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.mce_todo
def test_is_power_on(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

@pytest.mark.mce_todo
def test_is_vm_ready(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        raise NotImplementedError()

def test_get_vm_roles(vsphere_server, vcsim_settings):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        objects = client.get_all_vms()
        roles = client.get_vm_roles(objects[0])
        assert roles == ["ADMINISTRATOR"]

def test_resource_id(vsphere_server):
    url = vsphere_server

    with core.Client(host=url) as client:
        client.connect()
        dc = client.get_all_datacenters()[0]
        resource_id = client.resource_id(dc)
        assert resource_id == 'group-d1/datacenter-2'

