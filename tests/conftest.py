import pytest
import os

pytest_plugins = ['tests.mock_server']

# https://code.vmware.com/apis/968/vsphere

"""
Générer dynamiquement les terraforms et lancer la création
"""

def create_datacenter(dcname=None, service_instance=None, folder=None):
    """
    Creates a new datacenter with the given name.
    Any % (percent) character used in this name parameter must be escaped,
    unless it is used to start an escape sequence. Clients may also escape
    any other characters in this name parameter.
    An entity name must be a non-empty string of
    less than 80 characters. The slash (/), backslash (\) and percent (%)
    will be escaped using the URL syntax. For example, %2F
    This can raise the following exceptions:
    vim.fault.DuplicateName
    vim.fault.InvalidName
    vmodl.fault.NotSupported
    vmodl.fault.RuntimeFault
    ValueError raised if the name len is > 79
    https://github.com/vmware/pyvmomi/blob/master/docs/vim/Folder.rst
    Required Privileges
    Datacenter.Create
    :param folder: Folder object to create DC in. If None it will default to
                   rootFolder
    :param dcname: Name for the new datacenter.
    :param service_instance: ServiceInstance connection to a given vCenter
    :return:
    """
    if len(dcname) > 79:
        raise ValueError("The name of the datacenter must be under "
                         "80 characters.")
    if folder is None:
        folder = service_instance.content.rootFolder

    if folder is not None and isinstance(folder, vim.Folder):
        dc_moref = folder.CreateDatacenter(name=dcname)
        return dc_moref

def create_cluster(**kwargs):
    """
    Method to create a Cluster in vCenter
    :param kwargs:
    :return: Cluster MORef
    """
    cluster_name = kwargs.get("name")
    cluster_spec = kwargs.get("cluster_spec")
    datacenter = kwargs.get("datacenter")

    if cluster_name is None:
        raise ValueError("Missing value for name.")
    if datacenter is None:
        raise ValueError("Missing value for datacenter.")
    if cluster_spec is None:
        cluster_spec = vim.cluster.ConfigSpecEx()

    host_folder = datacenter.hostFolder
    cluster = host_folder.CreateClusterEx(name=cluster_name, spec=cluster_spec)
    return cluster

"""
dc = datacenter.create_datacenter(dcname=MY_ARGS.dcname, service_instance=SI)
cluster.create_cluster(datacenter=dc, name=MY_ARGS.cname)
"""
