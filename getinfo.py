from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl
from pyVmomi import vim
import getpass
import ssl
import atexit
import settings


def makeItGB(number):
    if number:
        return round(number/1024/1024/1024,2)
    else:
        return False


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
        print("Question  : ", summary.runtime.question.text)
    annotation = summary.config.annotation
    if annotation != None and annotation != "":
        print("Annotation : ", annotation)
    print("")


def main():
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode = ssl.CERT_NONE
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
            viewType = [vim.VirtualMachine]
            recursive = True
            containerView = content.viewManager.CreateContainerView(container,viewType,recursive)
            children = containerView.view

            for child in children:
                PrintVmInfo(child)
        except vmodl.MethodFault as error:
            print("Error:" + error.msg)
            return -1
    return 0


if __name__ == '__main__':
    main()
