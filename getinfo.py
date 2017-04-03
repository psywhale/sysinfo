from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl
from pyVmomi import vim

from datetime import date, datetime
import argparse
import getpass
import ssl
import atexit
import settings
import os
import sh

from jinja2 import Environment, PackageLoader, select_autoescape






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

    blank = open("template"+os.sep+"blank.md", "r")
    workingdir = args.workdir+"/drafts"

    vmMD = open(workingdir + os.sep + summary.config.name + ".md", "w")
    vmMD.write(blank.read())
    vmMD.close()


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
        vmMD = open(args.workdir+os.sep+"final"+os.sep+"virtual"+os.sep+summary.config.name+".md", "w")
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
        doc = envdrafts.get_template(summary.config.name + ".md")
    except:
        initializeTemplate(vm)
        doc = envdrafts.get_template(summary.config.name + ".md")
        if args.verbose:
            print("["+summary.config.name+"] draft not found.. Created blank at: "+args.workdir+os.sep+summary.config.name +
              ".md")

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
                PrintVmMD(child)


        except vmodl.MethodFault as error:
            print("Error:" + error.msg)
            return -1
    return 0

def checkdirs():
    if not os.path.isdir(args.workdir):
        if args.verbose:
            print("Creating directory "+args.workdir)
        os.makedirs(args.workdir)

    # if not os.path.isdir(args.outputdir):
    #     if args.verbose:
    #         print("Creating directory "+args.outputdir)
    #     os.makedirs(args.outputdir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Pulls basic info about virtual machines from a vcenter\n"
                                                 "and put it into a markdown formatted file template. This\n"
                                                 "\"draft\" can then be filled in by hand for what info that\n"
                                                 " can not be pulled from vcenter. "
                                                 "After all drafts are complete, "
                                                 "re-run this program to generate final documentation "
                                                 "from draft templates")
    parser.add_argument("workdir", help="working directory to store documentation drafts", default="drafts"
                        )

    parser.add_argument("-v", "--verbose",help="Be more verbose", action="store_true")

    args = parser.parse_args()
    env = Environment(loader=PackageLoader('getinfo', 'template'))
    blank = env.get_template("blank.md")
    checkdirs()
    gitstuff = sh.git.bake(_cwd=args.workdir)
    gitstuff.clone(settings.DRAFTREPO, "drafts")
    gitstuff.clone(settings.FINALREPO, "final")
    envdrafts = Environment(loader=PackageLoader('getinfo', args.workdir+"/drafts"))



    main()
