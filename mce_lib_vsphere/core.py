import logging
import ssl
import traceback
import re
import json
from typing import List, Tuple, Any, Mapping, Union

import typic
import arrow
from decouple import config
from furl import furl

from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect
from pyVmomi import vmodl  # VMODL: VMware Managed Object Design Language
from pyVmomi import vim, VmomiSupport

import requests

# TODO: typical 2.x : typic.api.strict_mode()

logger = logging.getLogger(__name__)

VCENTER_URL = config('MCE_VCENTER_URL', 'https://user1:pass@127.0.0.1:8989/sdk?timeout=120')
VCENTER_TIMEOUT = config("MCE_VCENTER_TIMEOUT", default=60, cast=int)  # 1mn

# TODO: se in get_vm_roles
ROLES = {
    -1: "Administrator",
    -4: "Anonymous",
    -5: "No Access",
    -2: "Read-Only",
    -3: "View",
}

# TODO: move to exceptions module
class FatalError(Exception):
    pass


class ConnectionError(Exception):
    pass


class VmNotFoundError(FatalError):
    pass


class NotPoweredError(FatalError):
    pass


class NotValidToolsError(FatalError):
    pass


class AuthenticationError(FatalError):
    pass


class GuestError(FatalError):
    pass


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
        timeout: int = VCENTER_TIMEOUT,
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
        self.timeout = timeout or VCENTER_TIMEOUT
        self.pool_size = 5
        self.debug = debug

        if host  and host.startswith("http"):
            self.parse_url(host)

        self.si = None
        self.content = None

        self.is_connected = False

    @typic.al
    def parse_url(self, url: str):
        """Parse settings with URL"""

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
    def connect(self) -> Tuple[vim.ServiceInstance, vim.ServiceInstanceContent]:
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

            return (self.si, self.content)

        except IOError as e:
            raise IOError("I/O error({0}): {1}".format(e.errno, e.strerror))
        except vim.fault.InvalidLogin:
            # 'Cannot complete login due to an incorrect user name or password.'
            msg = f"invalid authentication for [{self.username}]"
            raise AuthenticationError(msg)
        except vmodl.MethodFault as e:
            if self.debug:
                traceback.print_exc()
            msg = f"Connection could not be established for host [{self.host}:{self.port}] with timeout [{self.timeout}]"
            raise ConnectionError(msg)
        except Exception as e:
            self.is_connected = False
            if self.debug:
                traceback.print_exc()
            raise

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

        # TODO: version avec que l'id sans le typee avant
        parents = []
        self.recursive_parents(obj, parents)
        return "/".join([p._moId for p in parents]).lower()

    @typic.al(delay=True)
    def get_object_by_name(
        self, object_type: object, name: Union[str, re.Pattern], regex: bool = False
    ):
        """
        Get the vsphere object associated with a given text name
        Source: https://github.com/rreubenur/vmware-pyvmomi-examples/blob/master/create_template.py
        """
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

    def get_current_session(self) -> Mapping:
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
        data["loginTime"] = arrow.get(data["loginTime"]).for_json()
        return data

    @typic.al(delay=True)
    def get_vm_by_name(
        self, name: str, regex: bool = True, raise_error: bool = False
    ) -> vim.VirtualMachine:
        """
        Get a VM by its name
        """
        search = re.compile("^%s$" % name, re.IGNORECASE)
        vm = self.get_object_by_name(vim.VirtualMachine, search, regex=regex)
        if not vm and raise_error:
            msg = f"vm [{name}] not found in vcenter [{self.host}:{self.port}] for username [{self.username}]"
            raise VmNotFoundError(msg)
        return vm

    # FIXME: object_type: LazyType
    @typic.al(delay=True)
    def get_all(
        self, container: Any, object_type: object, recursive=True
    ) -> List[Any]:
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
        # TODO: return type
        return list(vm.effectiveRole)

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

    def get_host_infos(self, host):
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
        """Get minimal informations of Datastore

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

    def get_custom_fields(self, vm: vim.VirtualMachine) -> Mapping:
        fields = {}
        for availableField in vm.availableField:

            if availableField.managedObjectType != vim.VirtualMachine:
                continue

            for customValue in vm.customValue:
                if availableField.key == customValue.key:
                    fields[availableField.name] = customValue.value

        return fields

    def getNICs(self, summary, guest):
        nics = {}
        for nic in guest.net:
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

    # def getNICs2(self, summary, guest):
    #     nics = {}
    #     for nic in guest.net:
    #         if nic.network:  # Only return adapter backed interfaces
    #             if nic.ipConfig is not None and nic.ipConfig.ipAddress is not None:
    #                 nics[nic.macAddress] = {}  # Use mac as uniq ID for nic
    #                 nics[nic.macAddress]['netlabel'] = nic.network
    #                 ipconf = nic.ipConfig.ipAddress
    #                 i = 0
    #                 nics[nic.macAddress]['ipv4'] = {}
    #                 for ip in ipconf:
    #                     if ":" not in ip.ipAddress:  # Only grab ipv4 addresses
    #                         nics[nic.macAddress]['ipv4'][i] = ip.ipAddress
    #                         nics[nic.macAddress]['prefix'] = ip.prefixLength
    #                         nics[nic.macAddress]['connected'] = nic.connected
    #                 i = i+1
    #     return nics

    """
		data = {
			"session": client.get_current_session(),
			"vcenter": client.vcenter_infos(),
		}

    """

    @typic.al
    def _get_vm_infos(self, vm: vim.VirtualMachine) -> Mapping:
        summary = vm.summary
        guest = vm.guest
        #vm_config = vm.config
        vmsum = {}
        config = summary.config
        net = self.getNICs(summary, guest)
        vmsum['name'] = vm.name
        vmsum['hostname'] = vm.guest.hostName
        vmsum['is_template'] = config.template
        vmsum['mem'] = config.memorySizeMB / 1024
        vmsum['diskGB'] = summary.storage.committed / 1024**3
        vmsum['cpu'] = config.numCpu
        vmsum['path'] = config.vmPathName
        vmsum['ostype'] = config.guestFullName
        vmsum['state'] = summary.runtime.powerState
        vmsum['annotation'] = config.annotation if config.annotation else ''
        vmsum['net'] = net
        vmsum['fields'] = self.get_custom_fields(vm)
        vmsum['boot_time'] = summary.runtime.bootTime # FIXME: arrow.get(summary.runtime.bootTime).for_json()

        vmsum['guestFamily'] = guest.guestFamily    # 'otherGuestFamily',
        vmsum['toolsVersion'] = guest.toolsVersion  # '2147483647',

        if getattr(guest, 'toolsVersionStatus2', None):
            vmsum['toolsVersionStatus'] = guest.toolsVersionStatus2
        elif getattr(guest, 'toolsVersionStatus', None):
            vmsum['toolsVersionStatus'] = guest.toolsVersionStatus 

        if hasattr(guest, 'toolsStatus2'):
            vmsum['toolsStatus'] = guest.toolsStatus2    # 'toolsOk',
        elif hasattr(guest, 'toolsStatus'):
            vmsum['toolsStatus'] = guest.toolsStatus    # 'toolsOk',

        vmsum['toolsRunningStatus'] = guest.toolsRunningStatus    # ?
        vmsum['guestState'] = guest.guestState      # 'running',
        vmsum['guestOperationsReady'] = guest.guestOperationsReady # true
        vmsum['interactiveGuestOperationsReady'] = guest.interactiveGuestOperationsReady    # false,
        vmsum['guestStateChangeSupported'] = guest.guestStateChangeSupported  # true,
        return vmsum

    @typic.al
    def get_vm_infos(self, vm: vim.VirtualMachine) -> Mapping:
        return {
            "vm": self._get_vm_infos(vm),
            "properties": self.dump_to_dict(vm)
        }
