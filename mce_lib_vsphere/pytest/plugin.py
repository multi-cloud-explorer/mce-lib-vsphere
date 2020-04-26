import os
import shutil
import signal
import subprocess as sp
import time
import socket

from pyVim import connect

import pytest

HERE = os.path.dirname(__file__)
LOCAL_VCSIM = os.path.join(HERE, '..', '..', 'utils', 'vcsim')

def pytest_configure(config):
    config.addinivalue_line("markers", "mce_known_bug: mark test as known bug")
    config.addinivalue_line("markers", "mce_todo: mark todo")

def get_free_tcp_port(port=1024, max_port=65535):
    """Return free tcp port"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while port <= max_port:
        try:
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            port += 1
    raise IOError('no free ports')

@pytest.fixture(scope="session")
def vcsim_settings():
    vcsim_path = shutil.which('vcsim')
    if  not vcsim_path:
        vcsim_path = LOCAL_VCSIM
        if not os.path.exists(vcsim_path):
            raise AssertionError("vcsim tools is not found")
    return dict(
        vcsim_path=vcsim_path,
        api_version="6.5",
        username="user1",
        password="pass",
        datacenters=2,
        clusters=2, # datacenters * 2
        datastores=4,
        storages=2,
        pools=1,
        hosts=3,    # 14 ???
        vms=10, # 60
        vapps=2,
        opaque_networks=1
    )
    # 10 resource pool

# TODO: args en ligne de commande

def start_service(service_name, host, port, vcsim_settings):
    # TODO: convert

    vcsim_settings["host"] = host
    vcsim_settings["port"] = port

    args = "%(vcsim_path)s -api-version %(api_version)s -dc %(datacenters)s -cluster %(clusters)s -pool %(pools)s -host %(hosts)s -ds %(datastores)s -pod %(storages)s -vm %(vms)s -app %(vapps)s -nsx %(opaque_networks)s -l %(host)s:%(port)s -username %(username)s -password %(password)s -trace" % vcsim_settings
    # vcsim -api-version 6.5 -dc 2 -cluster 2 -pool 1 -host 3 -ds 4 -pod 2 -vm 10 -l 127.0.0.1:1024 -username user1 -password pass -trace

    process = sp.Popen(args.split(), stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.DEVNULL)

    for i in range(0, 30):
        if process.poll() is not None:
            break

        try:
            si = connect.SmartConnect(host=host, port=port, protocol='https', user=vcsim_settings["username"], pwd=vcsim_settings["password"], connectionPoolTimeout=2)
            break
        except IOError as err:
            time.sleep(0.5)
    else:
        stop_process(process)  # pytest.fail doesn't call stop_process
        pytest.fail("Can not start service: {}".format(service_name))

    return process


def stop_process(process):
    try:
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=5)
    except sp.TimeoutExpired:
        process.kill()
        outs, errors = process.communicate(timeout=5)
        exit_code = process.returncode
        msg = "Child process finished {} not in clean way: {} {}" .format(exit_code, outs, errors)
        raise RuntimeError(msg)

@pytest.yield_fixture(scope="session")
def vsphere_server(vcsim_settings):
    host = "127.0.0.1"
    port = get_free_tcp_port()
    username = vcsim_settings['username']
    password = vcsim_settings['password']
    url = f"https://{username}:{password}@{host}:{port}/sdk"
    process = start_service('vsphere', host, port, vcsim_settings)
    yield url
    stop_process(process)

