#!/bin/python3

import argparse
import sys,os,time
import subprocess
import uuid
# import pprint
# p_print=pprint.PrettyPrinter(indent=4).pprint

def monthname(nb,month):
    return '{:02d} {}'.format(nb+1,month)

months=['Janvier','Fevrier','Mars','Avril','Mai','Juin','Juillet','Aout','Septembre','Octobre','Novembre','Decembre']
emonth={"Jan":0,"Feb":1,"Mar":2,"Apr":3,"May":4,"Jun":5,"Jul":6,"Aug":7,"Sep":8,"Oct":9,"Nov":10,"Dec":11}
i,imonths=0,[]
for m in months:
    imonths+=[monthname(i,m)]
    i+=1

def dprint(text):
    pass

def makeFolders(args):
    dprint("Making sub folders")
    if len(args)==0:
        raise IndexError("Path argument not found")
    path=args[0]
    for d in imonths:
        p=os.path.join(path,d)
        os.mkdir(p)

def maketest(args):
    dprint("Making test files")
    try:
        os.mkdir("test")
    except:
        pass
    for i in range(12):
        r=subprocess.call(["touch","-m",'--date=2020-{:02d}-{:02d} 23:05:43.443117094 +0400'.format(i+1,i+2), "test/file{0:02d}.txt".format(i)])
    dprint("Test file made")

def makeBackup(args):
    dprint("Starting backup process...")
    if len(args)<2:
        raise IndexError("Path argument not found")
    listbackup=[]
    root=args[0]
    dest=args[1]
    if root.startswith(dest):
        raise IndexError("Destination path can't be part of the backup path")
    l=os.listdir(root)
    if len(l)==0:
        raise IndexError("Directory is empty")
    for f in l:
        f=os.path.join(root,f)
        t=os.path.getmtime(f)
        month=time.strftime("%b",time.gmtime(t))
        nmonth=emonth[month]
        nyear=time.strftime("%Y",time.gmtime(t))
        listbackup+=[makecommand(f,dest,nmonth,nyear)]
        # print(f,month,nmonth,nyear)
    # p_print(listbackup
    dprint("Executing subcommands")
    for l in listbackup:
        dprint("   "+' '.join(l))
        subprocess.call(l)


def updateFolders(args):
    if len(args)==0:
        raise IndexError("Path argument not found")
    dest=args[0]
    dprint("Updating folder {}".format(dest))
    l=os.listdir(dest)
    for fold in l:
        foldp=os.path.join(dest,fold)
        if os.path.isdir(foldp):
            for file in os.listdir(foldp):
                filep=os.path.join(foldp,file)
                if not os.path.isdir(filep):
                    t=time.strftime("%D %H:%M:%S +0000",time.gmtime(os.path.getmtime(filep)))
                    dprint("Updating {} with date {}".format(foldp,t))
                    subprocess.call(["touch","-m","--date="+t, foldp])
                    break

def finddest(dest,name):
    id=2
    try:
        name,ext=name.split(".",1)
        dname=os.path.join(dest,name+"."+ext)
        while os.path.exists(dname):
            dname=os.path.join(dest,"{} - {}.{}".format(name,id,ext))
            id+=1
    except:
        dname=os.path.join(dest,name)
        while os.path.exists(dname):
            dname=os.path.join(dest,"{} - {}".format(name,id))
            id+=1
    return dname

def makecommand(file,dest,nmonth,nyear):
    fy=os.path.join(dest,nyear)
    destmonth=os.path.join(fy,monthname(nmonth,months[nmonth]))
    if not os.path.exists(fy):
        dprint("Destination year doesn't exists...making directory ({})".format(fy))
        os.mkdir(fy)
    if not os.path.exists(destmonth):
        dprint("Dest month doesn't exists...making directory ({})".format(destmonth))
        os.mkdir(destmonth)
    pathdest=finddest(destmonth,os.path.basename(file))
    return ["mv","-n",file,pathdest]

commands={"make":makeFolders,"backup":makeBackup,"test":maketest,"update":updateFolders}

parser = argparse.ArgumentParser(description='Make backup folders.')
parser.add_argument('command',help='Command from list',choices=list(commands.keys()))
parser.add_argument('args',nargs='*',help='Arguments')
parser.add_argument('--verbose',action="store_true",default=True)
parser.add_argument("--quiet",action="store_false",dest="verbose")
parser.add_argument("--noupdate",action="store_true",default=False)
parser.add_argument("--dry",action="store_true",default=False)
# parser.add_argument("--months",default([1,2,3,4,5,6,7,8,9,10,11,12]))
parser.add_argument("--year",default=2019,type=int)

if __name__ == '__main__':
    p=parser.parse_args()
    # print(p.command)
    # print(commands[p.command](p.args))
    if p.verbose:
        def dprint(text):
            print(text)
    try:
        if not p.noupdate:
            updateFolders(p.args)
        commands[p.command](p.args)
    except FileNotFoundError as e:
        print(e)
    except IndexError as e:
        print(e)
    # except IOError as e:
    #     print(e)

    dprint("Program exited sucessfully")
