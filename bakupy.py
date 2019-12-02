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

def makeFolders(p):
    "Making all the subfolders corresponding to all months in a year"
    dprint("Making sub folders")

    args=p.args
    if len(args)==0:
        raise IndexError("Path argument not found")
    path=args[0]
    for d in imonths:
        p=os.path.join(path,d)
        os.mkdir(p)

def maketest(p):
    "Making a bunch of test files in a destination folder"
    dprint("Making test files")

    args=p.args
    size=4
    try:
        os.mkdir("test")
    except:
        pass
    for j in range(size):
        for i in range(12):
            r=subprocess.call(["touch","-m",'--date=20{:02d}-{:02d}-{:02d} 23:05:43.443117094 +0400'.format(j,i+1,i+1), "test/file{0:02d}.txt".format(i+12*j)])
    dprint("Test file made")

def makeBackup(p):
    "Backup a folder toward a following destination"
    dprint("Starting backup process...")

    if not p.noupdate:
        updateFolder(p.args[0])
    args=p.args
    if len(args)<2:
        raise IndexError("Path argument not found")
    listbackup=[]
    root,dest=args[0],args[1]

    if dest.startswith(root):
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
    dprint("Executing subcommands")
    for l in listbackup:
        dprint("  > "+' '.join(l))
        subprocess.call(l)
    # for year in yearupdate:
    #     updateFolder(os.path.join(p.args[1],year))

def updateFolders(p):
    "Update a list of directories with the modification date inside"
    dprint("Updating folders")

    args=p.args
    if p.recursive: #Do a bottom first update
        pass
    if len(args)==0:
        raise IndexError("Path argument not found")
    for path in args:
        for root, dirs, files in os.walk(path, topdown=p.recursive):
            for dir in dirs:
                updateFolder(os.path.join(root,dir))

def updateFolder(dest):
    "Update one folder with the modified date in one of the files"
    # dprint("Updating folder {}".format(dest))
    for root, dirs, files in os.walk(dest,topdown=True):
        if len(files)==0:
            towalk=dirs
        else:
            towalk=files

        for f in towalk:
            filep=os.path.join(root,f)
            t=time.strftime("%D %H:%M:%S",time.gmtime(os.path.getmtime(filep)))
            dprint("  > Updating {} with date {}".format(dest,t))
            return subprocess.call(["touch","-m","--date="+t, dest])

def initFiles(p):
    "Assume all files are in the right folders, and the folders are rightfully named"
    if len(p.args)==0:
        raise IndexError("Path argument not found")
    for arg in p.args:
        initFile(arg,p)

def initFile(dest,p):
    years=os.listdir(dest)
    itime=p.time
    for year in years:
        #Check sanity of year
        try:
            iyear=int(year)
        except ValueError: # Recuse on all folders ?
            raise IndexError("You are trying to update a folder not properly formatted")

        if iyear > 3000 or iyear < 1800:
            raise IOError("Year found is likely incorrect")
        months=os.listdir(os.path.join(dest,year))
        for month in months:
            imonth=int(month.split(" ")[0])
            if imonth<1 or imonth>12:
                raise IOError("Month not in valid range")
            path=os.path.join(dest,year,month)
            for root, dirs, files in os.walk(path, topdown=p.recursive):
                for f in dirs+files:
                    date="{:02d}/{:02d}/20 {}".format(iyear,imonth,itime)
                    des=os.path.join(dest,root,f)
                    dprint("  > Updating {} with date {}".format(f,date))
                    subprocess.call(["touch","-m","--date="+date, des])
    updateFolders(p) # It is "cleaner" even if less effective

def finddest(dest,name):
    "Find a non existing Destination name, will append a ' N' before the extention. Very uglyly made."
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
    "Make a move command, don't actually execute it. Return a list for subprocess."
    fy=os.path.join(dest,nyear)
    destmonth=os.path.join(fy,monthname(nmonth,months[nmonth]))
    if not os.path.exists(fy):
        dprint(" > Destination year doesn't exists...making directory ({})".format(fy))
        os.mkdir(fy)
    if not os.path.exists(destmonth):
        dprint("  > Dest month doesn't exists...making directory ({})".format(destmonth))
        os.mkdir(destmonth)
        # print(["touch","-m","--date=01/{:02d}/{}".format(nmonth+1,nyear), destmonth])
        # print(file,dest,nmonth,nyear)
    yearupdate.add(nyear)
    pathdest=finddest(destmonth,os.path.basename(file))
    return ["mv","-n",file,pathdest]


commands={"make":makeFolders,"backup":makeBackup,"test":maketest,"update":updateFolders,"init":initFiles}

parser = argparse.ArgumentParser(description='Make backup folders.')
parser.add_argument('command',help='Command from list',choices=list(commands.keys()))
parser.add_argument('args',nargs='*',help='Arguments')
parser.add_argument('--verbose',action="store_true",default=True)
parser.add_argument("--quiet",action="store_false",dest="verbose")
parser.add_argument("--recursive",action="store_true",default=False)
parser.add_argument("--noupdate",action="store_true",default=False)
parser.add_argument("--dry",action="store_true",default=False)
parser.add_argument("--time",default="10:10:10")

# parser.add_argument("--months",default([1,2,3,4,5,6,7,8,9,10,11,12]))
parser.add_argument("--year",default=2019,type=int)

yearupdate=set()
if __name__ == '__main__':
    p=parser.parse_args()
    errors=0
    if p.verbose:
        def dprint(text):
            print(text)
    try:
        commands[p.command](p)

    except FileNotFoundError as e:
        errors+=1
        print(e)
    except IndexError as e:
        errors+=1
        print(e)
    if errors:
        dprint("Program exited with errors")
    else:
        dprint("Program exited sucessfully")
