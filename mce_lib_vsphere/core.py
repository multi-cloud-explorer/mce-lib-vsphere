import logging
import ssl
import traceback
import re
import json
from typing import List, Tuple, Any, Mapping, Union
from enum import Enum, IntEnum, unique

import typic
from decouple import config
from furl import furl

from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect
from pyVmomi import vim, VmomiSupport
from pyVmomi import Iso8601

import requests

from  .exceptions import *

#FIXME: typic.api.strict_mode()

logger = logging.getLogger(__name__)

VCENTER_URL = config('MCE_VCENTER_URL', 'https://user1:pass@127.0.0.1:8989/sdk?timeout=120')

@unique
class ResourceTypes(str, Enum):
    DATACENTER = "vmware/Datacenter"
    VIRTUAL_APP = "vmware/VirtualApp"
    CLUSTER_COMPUTE_RESOURCE = "vmware/ClusterComputeResource"
    FOLDER = "vmware/Folder"
    DISTRIBUTED_VIRTUAL_PORTGROUP = "vmware/DistributedVirtualPortgroup"
    HOST_SYSTEM = "vmware/HostSystem"
    VIRTUAL_MACHINE = "vmware/VirtualMachine"
    NETWORK = "vmware/Network"
    OPAQUE_NETWORK = "vmware/OpaqueNetwork"
    RESOURCE_POOL = "vmware/ResourcePool"
    COMPUTE_RESOURCE = "vmware/ComputeResource" # ESX ?
    DATASTORE = "vmware/Datastore"
    DISTRIBUTED_VIRTUAL_SWITCH = "vmware/DistributedVirtualSwitch"

    @classmethod
    def to_choices(cls):
        return [(e.value, e.name) for e in cls]

    @classmethod
    def to_dict(cls, reverse=False):
        if reverse:
            return {e.value: e.name for e in cls}
        return {e.name: e.value for e in cls}

@unique
class EffectiveRoles(IntEnum):
    ADMINISTRATOR = -1
    READ_ONLY = -2
    VIEW = -3
    ANONYMOUS = -4
    NO_ACCESS = -5

    @classmethod
    def to_choices(cls):
        return [(e.value, e.name) for e in cls]

    @classmethod
    def to_dict(cls, reverse=False):
        if reverse:
            return {e.value: e.name for e in cls}
        return {e.name: e.value for e in cls}


class Client:
    """Client SDK for Vcenter"""

    @typic.al
    def __init__(
        self,
        host: str = None, #     host or url
        port: int = 443,
        path: str = '/sdk',
        username: str = None,
        password: str = None,
        is_ssl=True,
        verify: bool = True,
        debug: bool = False,
        timeout: int = 60,
    ):
        """
        Connect to a vCenter via the API

        **Examples:**

        >>> with Client(host="vcenter.mydomain.com", username="adminuser", password="adminpasswd") as cli:
        >>>     vm = cli.get_vm_by_name("myvm")
        >>>     print(vm.name)

        >>> cli = Client(host="vcenter.mydomain.com", username="adminuser", password="adminpasswd")
        >>> cli.connect()
        >>> vm = cli.get_vm_by_name("myvm")
        >>> print(vm.name)
        >>> cli.disconnect()

        :param host: Hostname or IP of the vCenter
        :type host: str or unicode
        :param port: Port on which the vCenter API is running (default: 443)
        :type port: int
        :param username: Username
        :type user: str or unicode
        :param password: Password
        :type user: str or unicode
        :param verify: Whether to verify SSL certs upon connection (default: False)
        :type verify: bool
        :param debug: Debug option (default: False)
        :type debug: bool
        :param timeout: Timeout in seconds (default: 60)
        :type timeout: int

        """
        self.host = host or VCENTER_URL
        self.port = port
        self.path = path
        self.username = username
        self.password = password
        self.is_ssl = is_ssl
        self.verify = verify
        self.timeout = timeout
        self.pool_size = 5
        self.debug = debug

        if host  and host.startswith("http"):
            self.parse_url(host)

        self.si = None
        self.content = None

        self.is_connected = False

    @typic.al
    def parse_url(self, url: str):
        """Parse settings with URL

        Args:
            url: Full url for connect to Vcenter

        """

        url = furl(url)

        if url.scheme == "http": # url.origin.startswith('http:'):
            self.is_ssl = False

        self.host = url.host
        self.port = url.port

        if str(url.path):
            self.path = str(url.path)

        self.username = url.args.get('username') or url.username
        self.password = url.args.get('password') or url.password

        if url.args.get('verify', '0') in ["false", "False", "0"]:
            self.verify = False

        if url.args.get('debug', '0') in ["true", "True", "1"]:
            self.debug = True

        if url.args.get('timeout'):
            self.timeout = int(url.args.get('timeout'))

        if url.args.get('pool_size'):
            self.pool_size = int(url.args.get('pool_size'))

        return url

    def __enter__(self):
        if not self.is_connected:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def disconnect(self):
        """Current session disconnect"""
        try:
            Disconnect(self.si)
        except Exception as err:
            logger.warning(str(err))

    @typic.al
    def connect(self):
        """Connect to Vcenter Server"""

        context = None
        protocol = 'http'
        if self.is_ssl:
            protocol = 'https'
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            if not self.verify:
                # Disable warnings about unsigned certificates
                context.verify_mode = ssl.CERT_NONE
                requests.packages.urllib3.disable_warnings()

        try:
            # TODO: certFile, certKeyFile, cacertsFile
            # TODO: connectionPoolTimeout:   Default value is 900 seconds (15 minutes).
            # TODO: mechanism='userpass'
            # TODO: poolSize=self.pool_size
            si = SmartConnect(
                host=self.host,
                user=self.username,
                pwd=self.password,
                port=self.port,
                path=self.path,
                protocol=protocol,
                sslContext=context,
                #preferredApiVersions = 'vim25', #GetServiceVersions('vim25'),
                connectionPoolTimeout=self.timeout,  # default 900 sec = 15mn
            )
            self.si = si
            self.content = si.RetrieveContent()
            self.is_connected = True

        except IOError as e:
            if self.debug:
                traceback.print_exc()
            msg = f"Connection could not be established for host [{self.host}:{self.port}] with timeout [{self.timeout}]"
            logger.error(msg)
            raise ConnectionError(msg)
            #raise IOError("I/O error({0}): {1}".format(e.errno, e.strerror))
        except vim.fault.InvalidLogin:
            # 'Cannot complete login due to an incorrect user name or password.'
            msg = f"invalid authentication for [{self.username}]"
            raise AuthenticationError(msg)
        # except vmodl.MethodFault as e:
        #     if self.debug:
        #         traceback.print_exc()
        #     msg = f"Connection could not be established for host [{self.host}:{self.port}] with timeout [{self.timeout}]"
        #     raise ConnectionError(msg)
        except Exception as err:
            self.is_connected = False
            if self.debug:
                traceback.print_exc()
            # TODO: add fields
            raise FatalError(str(err))

    @typic.al
    def dump_to_dict(self, obj) -> Mapping:
        return json.loads(json.dumps(obj, cls=VmomiSupport.VmomiJSONEncoder))

    def recursive_parents(self, obj, parents=[]):
        if obj.parent:
            self.recursive_parents(obj.parent, parents)
        parents.append(obj)
     
    @typic.al
    def resource_id(self, obj) -> str:
        """Build unique ID with obj._moId and parents"""

        # TODO: version avec que l'id sans le type avant
        parents = []
        self.recursive_parents(obj, parents)
        return "/".join([p._moId for p in parents]).lower()

    @typic.al(delay=True)
    def get_object_by_name(
        self, object_type: object, name: Union[str, re.Pattern], regex: bool = False
    ):

        # TODO: add filter -> https://github.com/vmware/pyvmomi-community-samples/blob/39bd95553df337ae35f1b101c487b37063967555/samples/filter_vms.py#L50
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, [object_type], True
        )
        for c in container.view:
            if regex:
                if re.match(name, c.name):
                    return c
            elif c.name == name:
                return c

    @typic.al
    def vcenter_infos(self) -> Mapping:
        """Return informations about Vcenter"""

        about = self.content.about
        return {
            "version": about.version,  # '6.5.0',
            "build": about.build,  # '7515524',
            "osType": about.osType,  # 'win32-x64',
            "apiType": about.apiType,  # 'VirtualCenter',
            "apiVersion": about.apiVersion,  # '6.5',
            "licenseProductName": about.licenseProductName,  # 'VMware VirtualCenter Server',
            "licenseProductVersion": about.licenseProductVersion,  # '6.0'
        }

    def get_current_session(self): # -> Mapping:
        currentSession = self.content.sessionManager.currentSession
        fields = [
            "userName",  # 'MyUserName'
            "fullName",  # 'My FullName'
            "ipAddress",  # '10.172.192.8'
            "userAgent",  # 'pyvmomi Python/3.6.8 (Linux; 3.10.0-862.11.6.el7.x86_64; x86_64)'
            "locale",  # 'en'
            "loginTime",  # datetime.datetime(2019, 7, 22, 13, 8, 49, 529086, tzinfo=<pyVmomi.Iso8601.TZInfo object at 0x7f65aeab7128>)
            "callCount"
        ]
        data = {field: getattr(currentSession, field, None) for field in fields}
        data["loginTime"] = Iso8601.ISO8601Format(data["loginTime"])
        # TODO: data["loginTime"] = arrow.get(login_time, "YYYY-MM-DD[T]HH:mm:ss.S").datetime
        return data

    @typic.al(delay=True)
    def search_vm_by_uuid(self, uuid: str, by_instance_uuid: bool = True) -> vim.VirtualMachine:
        """Search VirtualMachine by Instance UUID or Bios UUID

        Return None if  not found
        """

        search_index = self.content.searchIndex
        return search_index.FindByUuid(None, uuid, True, by_instance_uuid)

    @typic.al
    def get_vm_by_name(self, name: str, raise_error: bool = False) -> vim.VirtualMachine:
        """
        Get a VM by its name
        """
        # TODO: il peut y en avoir plusieurs ?
        search = re.compile("^%s$" % name, re.IGNORECASE)
        vm = self.get_object_by_name(vim.VirtualMachine, search, regex=True)
        if not vm and raise_error:
            msg = f"vm [{name}] not found in vcenter [{self.host}:{self.port}] for username [{self.username}]"
            raise VmNotFoundError(msg)
        return vm

    # FIXME: object_type: LazyType
    #@typic.al(delay=True)
    def get_all(
        self, container: Any, object_type: object, recursive=True
    ): # -> List[Any]
        """
        Get all items of a certain type
        Example: get_all(content, vim.Datastore) return all datastore objects
        """
        obj_list = list()
        view_manager = self.content.viewManager
        object_view = view_manager.CreateContainerView(
            container, [object_type], recursive
        )
        for obj in object_view.view:
            if isinstance(obj, object_type):
                obj_list.append(obj)
        object_view.Destroy()
        return obj_list

    @typic.al
    def get_all_folders(self) -> List[vim.Folder]:
        """Return List of folders children"""
        return self.get_all(self.content.rootFolder, vim.Folder)

    @typic.al
    def get_all_hosts(self) -> List[vim.HostSystem]:
        """
        Get all clusters on a vCenter
        """
        return self.get_all(self.content.rootFolder, vim.HostSystem)

    @typic.al
    def get_all_pools(self) -> List[vim.ResourcePool]:
        return self.get_all(self.content.rootFolder, vim.ResourcePool)

    @typic.al
    def get_all_clusters(self) -> List[vim.ClusterComputeResource]:
        """
        Get all hosts on a vCenter
        """
        return self.get_all(self.content.rootFolder, vim.ClusterComputeResource)
    
    @typic.al
    def get_all_datacenters(self) -> List[vim.Datacenter]:
        """
        Get all datacenter on a vCenter
        """
        return self.get_all(self.content.rootFolder, vim.Datacenter)

    @typic.al
    def get_all_datastores(self) -> List[vim.Datastore]:
        """
        Get all datastore on a vCenter
        """
        return self.get_all(self.content.rootFolder, vim.Datastore)

    @typic.al
    def get_all_vms(self) -> List[vim.VirtualMachine]:
        """
        Get all VMs managed by a vCenter
        """
        return self.get_all(self.content.rootFolder, vim.VirtualMachine)

    @typic.al
    def get_all_dvswitches(self) -> List[vim.DistributedVirtualSwitch]:
        """
        Get all the distributed switches
        """
        return self.get_all(self.content.rootFolder, vim.DistributedVirtualSwitch)

    @typic.al
    def get_all_dport_groups(self) -> List[vim.dvs.DistributedVirtualPortgroup]:
        """
        Get all the distributed port groups
        """
        return self.get_all(
            self.content.rootFolder, vim.dvs.DistributedVirtualPortgroup
        )

    @typic.al
    def get_all_virtualapps(self) -> List[vim.VirtualApp]:
        """
        Get all VirtualApp
        """
        return self.get_all(self.content.rootFolder, vim.VirtualApp)

    @typic.al
    def get_all_networks(self) -> List[vim.Network]:
        """
        Get all Network
        """
        return self.get_all(self.content.rootFolder, vim.Network)

    @typic.al
    def get_all_opaque_networks(self) -> List[vim.OpaqueNetwork]:
        """
        Get all OpaqueNetwork
        """
        return self.get_all(self.content.rootFolder, vim.OpaqueNetwork)

    @typic.al
    def get_all_compute_resources(self) -> List[vim.ComputeResource]:
        """
        Get all ComputeResource
        """
        return self.get_all(self.content.rootFolder, vim.ComputeResource)

    @typic.al
    def get_all_storage_pods(self) -> List[vim.StoragePod]:
        """
        Get all StoragePod
        """
        return self.get_all(self.content.rootFolder, vim.StoragePod)

    @typic.al
    def get_hosts_in_datacenter(self, datacenter) -> List[vim.HostSystem]:
        """
        Get all hosts belonging to a given datacenter
        """
        return self.get_all(datacenter, vim.HostSystem)

    @typic.al
    def get_vms_in_datacenter(self, datacenter) -> List[vim.VirtualMachine]:
        """
        Get all vms belonging to a given datacenter
        """
        return self.get_all(datacenter, vim.VirtualMachine)

    @typic.al
    def is_valid_run_tools(self, vm: vim.VirtualMachine) -> bool:
        if not self.is_power_on(vm):
            msg = f"vm {vm.name} is not powered"
            raise NotPoweredError(msg)
        if not self.is_valid_tools(vm):
            msg = f"no valid vm_tools state for {vm.name} - toolsStatus[{vm.guest.toolsStatus}] - guestState[{vm.guest.guestState}]"
            raise NotValidToolsError(msg)
        return True

    @typic.al
    def is_valid_tools(self, vm: vim.VirtualMachine) -> bool:
        if not vm:
            raise AttributeError("vm parameter is None")
        # tools_status == 'toolsNotInstalled' or tools_status == 'toolsNotRunning'
        return (
            vm.guest.toolsStatus in ["toolsOk", "toolsOld"]
            and vm.guest.guestState == "running"
        )

    @typic.al
    def is_power_on(self, vm: vim.VirtualMachine) -> bool:
        if not vm:
            raise AttributeError("vm parameter is None")
        return vm.summary.runtime.powerState == "poweredOn"

    @typic.al
    def is_vm_ready(
        self, name: str = None, vm: vim.VirtualMachine = None, raise_error: bool = True
    ) -> bool:
        """Check if vm exist and is ready for vmtools"""

        try:
            if not vm:
                vm = self.get_vm_by_name(name, raise_error=raise_error)
            return self.is_valid_run_tools(vm)
        except Exception as e:
            logger.warning(str(e))
            if raise_error:
                raise
            return False

        return True

    @typic.al
    def get_vm_roles(self, vm: vim.VirtualMachine) -> List[Any]:
        roles_by_value = EffectiveRoles.to_dict(True)
        roles = []
        for role in vm.effectiveRole:
            roles.append(roles_by_value[role])
        return roles

    def get_cluster_infos(self, cluster) -> Mapping:
        return {
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

    def get_host_infos(self, host) -> Mapping:
        product = host.config.product
        return {
            "name": host.name,
            "managementServerIp": host.summary.managementServerIp,
            "fullName": product.fullName,  # 'VMware ESXi 6.0.0 build-10474991',
            "version": product.version,  # '6.0.0',
            "apiVersion": product.apiVersion,  # '6.0',
        }

    def get_pool_infos(self, pool) -> Mapping:
        return {
            "name": pool.name,
        }

    def get_datastore_infos(self, datastore) -> Mapping:
        """Get minimal informations of Datastore"""

        """
        Example return:
        {
            'id': 'xxx',
            'name': 'LocalDS_0',
            'capacity': 3137323008,
            'freespace': -18341826560,
            'uncommitted': 0,
            'provisioned': 21479149568,
            'type': 'OTHER',
            'accessible': true,
            'maintenance_mode': 'normal'
        }
        """

        ds_capacity = datastore.summary.capacity
        ds_freespace = datastore.summary.freeSpace
        ds_uncommitted = datastore.summary.uncommitted or 0

        return {
            "id": datastore._moId,
            "name": datastore.name,
            "capacity": ds_capacity,
            "freespace": ds_freespace,
            "uncommitted": ds_uncommitted,
            "provisioned": (ds_capacity - ds_freespace) + ds_uncommitted,
            "type": datastore.summary.type,
            "accessible": datastore.summary.accessible,
            "maintenance_mode": datastore.summary.maintenanceMode
        }

    @typic.al
    def get_custom_fields(self, vm: vim.VirtualMachine) -> Mapping:
        fields = {}
        for availableField in vm.availableField:

            if availableField.managedObjectType != vim.VirtualMachine:
                continue

            for customValue in vm.customValue:
                if availableField.key == customValue.key:
                    fields[availableField.name] = customValue.value

        return fields

    @typic.al
    @typic.al
    def getNICs(self, vm: vim.VirtualMachine) -> Mapping:
        nics = {}
        for nic in vm.guest.net:
            if nic.network:  # Only return adapter backed interfaces
                if nic.ipConfig is not None and nic.ipConfig.ipAddress is not None:
                    nics[nic.macAddress] = {}  # Use mac as uniq ID for nic
                    nics[nic.macAddress]['netlabel'] = nic.network
                    ipconf = nic.ipConfig.ipAddress
                    i = 0
                    nics[nic.macAddress]['ipAddress'] = {}
                    for ip in ipconf:
                        if ":" not in ip.ipAddress:  # Only grab ipv4 addresses
                            nics[nic.macAddress]['ipAddress'][i] = ip.ipAddress
                            nics[nic.macAddress]['prefixLength'] = ip.prefixLength
                            nics[nic.macAddress]['connected'] = nic.connected
                            nics[nic.macAddress]['origin'] = ip.origin
                            nics[nic.macAddress]['state'] = ip.state
                    i = i+1
        return nics

    @typic.al
    def _get_vm_infos(self, vm: vim.VirtualMachine) -> Mapping:

        vmsum = {
            "boot_time": None,
            "create_date": None # Since vSphere API 6.7
        }
        vmsum['vm_path_name'] = vm.summary.config.vmPathName # '[LocalDS_0] DC0_H0_VM0/DC0_H0_VM0.vmx'

        vmsum['name'] = vm.name # TODO: vérifier si vm.name et config.name sont toujours pareil
        vmsum['uuid'] = vm.config.instanceUuid
        vmsum['bios_uuid'] = vm.config.uuid
        vmsum['hostname'] = vm.guest.hostName

        vmsum['is_template'] = vm.config.template

        vmsum['diskGB'] = vm.summary.storage.committed / 1024**3

        hardware = vm.config.hardware
        vmsum['cpu_count'] = hardware.numCPU
        vmsum['cpu_cores'] = hardware.numCoresPerSocket
        vmsum['mem_mb'] = hardware.memoryMB

        #vmsum['mem'] = vm.summary.config.memorySizeMB / 1024

        vmsum['ostype'] = vm.config.guestFullName

        vmsum['state'] = vm.summary.runtime.powerState

        vmsum['annotation'] = vm.config.annotation if vm.config.annotation else ''

        if not vm.config.template and getattr(vm.summary.runtime, "bootTime", None):
            vmsum['boot_time'] = Iso8601.ISO8601Format(vm.summary.runtime.bootTime)

        if getattr(vm.config, "createDate", None):
            vmsum['create_date'] = Iso8601.ISO8601Format(vm.config.createDate)

        vmsum['guestFamily'] = vm.guest.guestFamily    # 'otherGuestFamily',

        vmsum['toolsVersion'] = vm.guest.toolsVersion  # '2147483647',

        if getattr(vm.guest, 'toolsVersionStatus2', None):
            vmsum['toolsVersionStatus'] = vm.guest.toolsVersionStatus2
        elif getattr(vm.guest, 'toolsVersionStatus', None):
            vmsum['toolsVersionStatus'] = vm.guest.toolsVersionStatus

        if hasattr(vm.guest, 'toolsStatus2'):
            vmsum['toolsStatus'] = vm.guest.toolsStatus2    # 'toolsOk',
        elif hasattr(vm.guest, 'toolsStatus'):
            vmsum['toolsStatus'] = vm.guest.toolsStatus    # 'toolsOk',

        vmsum['toolsRunningStatus'] = vm.guest.toolsRunningStatus    # ?
        vmsum['guestState'] = vm.guest.guestState      # 'running',
        vmsum['guestOperationsReady'] = vm.guest.guestOperationsReady # true
        vmsum['interactiveGuestOperationsReady'] = vm.guest.interactiveGuestOperationsReady    # false,
        vmsum['guestStateChangeSupported'] = vm.guest.guestStateChangeSupported  # true,

        vmsum['net'] = self.getNICs(vm)

        vmsum['fields'] = self.get_custom_fields(vm)


        return vmsum

    @typic.al
    def get_vm_infos(self, vm: vim.VirtualMachine) -> Mapping:
        return {
            "vm": self._get_vm_infos(vm),
            "properties": self.dump_to_dict(vm)
        }
