from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl
from pyVmomi import vim
from datetime import date, datetime

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


def PrintCSVHead():
    print("host,name,path,guest,cpus,cores/socket,ramMB,Disk Qty, network, disk, state,Annotation")
    return


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
            PrintVmInfo(c, depth+1)
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

    vmMD = open(summary.config.name+".md", "w")

    vmMD.write("#Basic Documentation for "+summary.config.name+"\n")
    vmMD.write("###Document Versions:\n"
               "version 2  " + date.today().isoformat() + "\n")
    vmMD.write("###Summary\n")

    annotation = summary.config.annotation
    str(annotation).encode(encoding='utf-8')
    test = re.sub("[^A-Za-z#\n0-9. :]","",annotation)
    if annotation != None and annotation != "":
        vmMD.write(test+"\n")
    vmMD.write("###Software Information\n")
    vmMD.write("####General Information\n")
    vmMD.write("OS Name: " + summary.config.guestFullName + "\n\n")
    vmMD.write("CPU(s) : " + str(summary.config.numCpu) + "\n\n")
    vmMD.write("Cores per Socket: " + str(summary.vm.config.hardware.numCoresPerSocket) + "\n\n")
    vmMD.write("RAM: " + str(summary.config.memorySizeMB) + "\n\n")
    vmMD.write("Hard Drive: " + str(summary.config.numVirtualDisks) + "\n\n")
    disks = guest.disk
    for disk in disks:
        vmMD.write("* Mount: "+ disk.diskPath + "   \nSize (free/total): " +
                   str(makeItGB(disk.freeSpace)) + "/" + str(makeItGB(disk.capacity)) + "GB \n")


    vmMD.write("###Network Configuration\n")
    vmMD.write("####Management Configuration\n")
    vmMD.write("Management IP/Website : vcenter.campus.wosc.edu\n\n")
    vmMD.write("Management Port: 9443\n\n")
    vmMD.write("Perferred Method: VMware vSphere web client\n\n")
    
    vmMD.write("####IP Configuration\n")

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

def PrintVMCVS(vm, depth=1):
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
            PrintVmInfo(c, depth + 1)
        return

    # if this is a vApp, it likely contains child VMs
    # (vApps can nest vApps, but it is hardly a common usecase, so ignore that)
    if isinstance(vm, vim.VirtualApp):
        vmList = vm.vm
        for c in vmList:
            PrintVmInfo(c, depth + 1)
        return

    summary = vm.summary
    guest = vm.guest
    print(summary.runtime.host.name + "," + summary.config.name + "," + summary.config.vmPathName + "," +
          summary.config.guestFullName + "," +
          str(summary.config.numCpu) + "," +
          str(summary.vm.config.hardware.numCoresPerSocket) + "," +
          str(summary.config.memorySizeMB) + "," +
          str(summary.config.numVirtualDisks) + ","
          , end='')

    networks = guest.net
    disks = guest.disk

    for network in networks:
        if network.ipAddress:
            ipv4 = list(network.ipAddress)[0]
        else:
            ipv4 = None

        print("[", network.network, " IP ", str(ipv4).replace("\n", ""), " mac ", network.macAddress, "]", end='')


        print(",", end='')

    for disk in disks:
        print("[disk:", disk.diskPath, " Size: ", makeItGB(disk.freeSpace), "/", makeItGB(disk.capacity), "GB ]",
                  end='')
        print(",", end='')

        print(summary.runtime.powerState + ",", end="")

    if summary.runtime.question != None:
        False
        # print("Question  : ", summary.runtime.question.text)
    annotation = summary.config.annotation
    if annotation != None and annotation != "":
        print("\"" + annotation + "\"", end="")

    print("")


def PrintVmInfo(vm, depth=1):
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
            PrintVmInfo(c, depth+1)
        return

    # if this is a vApp, it likely contains child VMs
    # (vApps can nest vApps, but it is hardly a common usecase, so ignore that)
    if isinstance(vm, vim.VirtualApp):
        vmList = vm.vm
        for c in vmList:
            PrintVmInfo(c, depth + 1)
        return

    summary = vm.summary
    guest = vm.guest
    print("Host         : ", summary.runtime.host.name)
    print("Name         : ", summary.config.name)
    print("Path         : ", summary.config.vmPathName)
    print("Guest        : ", summary.config.guestFullName)
    print("Cpus         : ", summary.config.numCpu)
    print("Cores/Socket : ", summary.vm.config.hardware.numCoresPerSocket)
    print("RAM (MB)     : ", summary.config.memorySizeMB)
    print("Num of Disks : ", summary.config.numVirtualDisks)
    # summary.config.numVirtualDisks  summary.config.numEthernetCards
    # summary.runtime.host.name summary.host.hardware.model
    # summary.guest.hostName summary.vm.config.hardware.device.13.macAddress
    # summary.storage.committed summary.storage.uncommitted
    #
    #devices = summary.vm.config.hardware.device
    # for device in devices:
    #     if type(device).__name__ == "vim.vm.device.VirtualE1000" or type(device).__name__ == "vim.vm.device.VirtualVmxnet3":
    #         print("Network Card :", device.deviceInfo.label)
    #         print("MAC        :", device.macAddress)
    networks = guest.net
    disks = guest.disk

    for network in networks:
        if network.ipAddress:
            ipv4 = list(network.ipAddress)[0]
        else:
            ipv4 = None
        print("Net: ", network.network, " IP: ", str(ipv4).replace("\n", ""), "MAC: ", network.macAddress)

    for disk in disks:
        print("disk:\t", disk.diskPath, "\tSize: ", makeItGB(disk.freeSpace), "/", makeItGB(disk.capacity), "GB")
    print("State      : ", summary.runtime.powerState)

    if summary.runtime.question != None:
        False
        #print("Question  : ", summary.runtime.question.text)
    annotation = summary.config.annotation
    if annotation != None and annotation != "":
        print("Annotation : ", annotation)

    print("")


def main():
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode = ssl.CERT_NONE
    if not settings.PASSWORD:
        settings.PASSWORD = getpass.getpass("Password:")
    if settings.OUTPUT is "CSV":
        PrintCSVHead()

    for host in settings.HOSTS:
        try:
            si = SmartConnect(host=host, user=settings.USER, pwd=settings.PASSWORD, sslContext=context)
            if not si:
                print("could not connect to ", host)
             #   return -1
            atexit.register(Disconnect, si)
            content = si.RetrieveContent()
            container = content.rootFolder
            viewType = [vim.VirtualMachine]
            recursive = True
            containerView = content.viewManager.CreateContainerView(container,viewType,recursive)
            children = containerView.view

            for child in children:
                if settings.OUTPUT is "CVS":
                    PrintVMCVS(child)
                elif settings.OUTPUT is 'MD':
                    PrintVmMD(child)
                else:
                    PrintVmInfo(child)

        except vmodl.MethodFault as error:
            print("Error:" + error.msg)
            return -1
    return 0


if __name__ == '__main__':
    main()
