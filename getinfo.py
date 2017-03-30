from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl
from pyVmomi import vim

from datetime import date, datetime
import argparse
import getpass
import ssl
import atexit
import settings


from jinja2 import Environment, PackageLoader, select_autoescape
env = Environment(loader=PackageLoader('getinfo','template'))
blank = env.get_template("blank.md")





def makeItGB(number):
    if number:
        return round(number/1024/1024/1024, 2)
    else:
        return False


def initializeTemplate(vm, depth=1):
    """
    Create templates for each vm to be modifed by hand for info unavailable via sdk
    :param vm:
    :param depth:
    :return:
    """

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

    blank = open("template/blank.md", "r")

    vmMD = open("template/" + summary.config.name + ".md", "w")
    vmMD.write(blank.read())


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
    data = {}

    data["name"] = summary.config.name
    data["date"] = date.today().isoformat()
    data["summary"] = str(summary.config.annotation)
    data["os"] = summary.config.guestFullName
    data["cpucount"] = str(summary.config.numCpu)
    data["socket"] = str(summary.vm.config.hardware.numCoresPerSocket)
    data["memory"] = str(summary.config.memorySizeMB) + " MB"
    data["numDisks"] = str(summary.config.numVirtualDisks)

    disksraw = guest.disk
    info = {}
    disks = []


    for disk in disksraw:

        info["capacity"] = str(makeItGB(disk.capacity)) + " GB"
        info["diskPath"] = disk.diskPath

        disks.append(info)
        info = {}

    data["disks"] = disks




    networksraw = guest.net

    info = {}
    networks = []
    for network in networksraw:

        if network.ipAddress:
            ipv4 = list(network.ipAddress)[0]
            info["ipv4"] = str(ipv4).replace("\n", "")
        else:
            info["ipv4"] = None
        if network.macAddress:
            info["mac"] = network.macAddress
        else:
            info["mac"] = None

        info["network"] = network.network
        networks.append(info)
        info = {}

    data["Net"] = networks
    try:
        doc = env.get_template(summary.config.name + ".md")
    except:
        initializeTemplate(vm)
        doc = env.get_template(summary.config.name + ".md")
        print("Uhh "+summary.config.name+" template was not there.. made one for you. \n You will need to modify it"
                                         " as it is blank")

    vmMD.write(doc.render(data))
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
                if args.init:
                    initializeTemplate(child)
                else:
                    PrintVmMD(child)


        except vmodl.MethodFault as error:
            print("Error:" + error.msg)
            return -1
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--init", help="Creates Blank templates for each VM found. "
                                             "Stored in ./template to use to create docs. These then can be modified"
                                             " by hand.",
                        action="store_true")
    args = parser.parse_args()
    main()
