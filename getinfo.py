from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl
from pyVmomi import vim
from datetime import date, datetime

from jinja2 import Environment, PackageLoader, select_autoescape

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



    vmMD.write("# Basic Documentation for "+summary.config.name+"\n")
    vmMD.write("### Document Versions:\n"
               "version 2  " + date.today().isoformat() + "\n")
    vmMD.write("### Summary\n")

    annotation = summary.config.annotation
    str(annotation).encode(encoding='utf-8')
    test = re.sub("[^A-Za-z#\n0-9. :*_><\[\](),!;?'\"]", "", annotation)
    if annotation != None and annotation != "":
        vmMD.write(test+"\n")
    vmMD.write("### Software Information\n")
    vmMD.write("#### General Information\n")
    vmMD.write("OS Name: " + summary.config.guestFullName + "\n\n")
    vmMD.write("CPU(s) : " + str(summary.config.numCpu) + "\n\n")
    vmMD.write("Cores per Socket: " + str(summary.vm.config.hardware.numCoresPerSocket) + "\n\n")
    vmMD.write("RAM: " + str(summary.config.memorySizeMB) + "\n\n")
    vmMD.write("Hard Drive: " + str(summary.config.numVirtualDisks) + "\n\n")
    disks = guest.disk

    for disk in disks:
        disk.capacity = str(makeItGB(disk.capacity))
        vmMD.write("* Mount: "+ disk.diskPath + disk.capacity + "GB \n")



    networks = guest.net
    for network in networks:
        if network.ipAddress:
            ipv4 = list(network.ipAddress)[0]
        else:
            ipv4 = None
        if network.macAddress:
            mac = network.macAddress
        else:
            mac = None
        try:
            vmMD.write("* Net: " + network.network + " IP: " + str(ipv4).replace("\n", "") +
                   " MAC: " + str(mac) + "\n")
        except:
            print("ERROR! ",summary.config.name, " no mac?")

    vmMD.close()


def main():
    env = Environment(loader=PackageLoader('getinfo','template'))
    blank = env.get_template("blank.md")
    print(blank.render())
    exit()
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
