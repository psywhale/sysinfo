from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl
from pyVmomi import vim
from pyVmomi.VmomiSupport import LazyObject
from datetime import date, datetime

from jinja2 import Environment, PackageLoader, select_autoescape
env = Environment(loader=PackageLoader('getinfo','template'))
blank = env.get_template("blank.md")

from os import getcwd, access

import argparse



import getpass
import ssl
import atexit
import settings
import re


def makeItGB(number):
    if number:
        return round(number/1024/1024/1024, 2)
    else:
        return False




def PrintVmMD(vm, depth=1):
    """
    Print information for a particular virtual machine or recurse into a folder
    or vApp with depth protection
    """
    maxdepth = 10




    # if this is a group it will have children. if it does, recurse into them
    # and then return
    if hasattr(vm, 'childEntity'):
        if depth > maxdepth:
            return
        vmList = vm.childEntity
        for c in vmList:
            PrintVmMD(c, depth+1)
        return

    # if this is a vApp, it likely contains child VMs
    # (vApps can nest vApps, but it is hardly a common usecase, so ignore that)
    if isinstance(vm, vim.VirtualApp):
        vmList = vm.vm
        for c in vmList:
            PrintVmMD(c, depth + 1)
        return

    summary = vm.summary
    guest = vm.guest

    try:
        vmMD = open(settings.OUTPUTDIR+summary.config.name+".md", "w")
    except PermissionError:
        print("File permission error")
        raise
    data = LazyObject()

    data.name = summary.config.name
    data.date = date.today().isoformat()
    data.summary = str(summary.config.annotation).encode(encoding='utf-8')
    data.os = summary.config.guestFullName
    data.cpucount = str(summary.config.numCpu)
    data.socket = str(summary.vm.config.hardware.numCoresPerSocket)
    data.memory = str(summary.config.memorySizeMB) + " MB"
    data.numDisks = str(summary.config.numVirtualDisks)


    disksraw = guest.disk
    disks = LazyObject()
    x = 0

    for disk in disksraw:

        disks[x].capacity = str(makeItGB(disk.capacity))
        disks[x].diskPath = disk.diskPath

        x.__add__(1)
        # vmMD.write("* Mount: "+ disk.diskPath + disk.capacity + "GB \n")

    data.disks = disks



    networksraw = guest.net
    x = 0
    networks = []
    for network in networksraw:
        networks.append(x)
        if network.ipAddress:
            ipv4 = list(network.ipAddress)[0]
            networks[x].ipv4 = str(ipv4).replace("\n", "")
        else:
            networks[x].ipv4 = None
        if network.macAddress:
            networks[x].mac = network.macAddress
        else:
            networks[x].mac = None

        networks[x].network = network.network
        x.__add__(1)

    data.Net = networks

    vmMD.write(blank.render(data))
    vmMD.close()


def main():

    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode = ssl.CERT_NONE
    if not settings.PASSWORD:
        settings.PASSWORD = getpass.getpass("Password:")


    for host in settings.HOSTS:
        try:
            si = SmartConnect(host=host, user=settings.USER, pwd=settings.PASSWORD, sslContext=context)
            if not si:
                print("could not connect to ", host)
            #   return -1
            atexit.register(Disconnect, si)
            content = si.RetrieveContent()
            container = content.rootFolder
            viewtype = [vim.VirtualMachine]

            recursive = True
            containerView = content.viewManager.CreateContainerView(container, viewtype, recursive)
            children = containerView.view

            for child in children:
                PrintVmMD(child)


        except vmodl.MethodFault as error:
            print("Error:" + error.msg)
            return -1
    return 0


if __name__ == '__main__':
    main()
