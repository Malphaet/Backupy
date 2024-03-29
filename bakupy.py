#!/usr/bin/env python3

import argparse
import sys,os,time
import subprocess
import datetime
import uuid

# Platform Detection
# Add a rsync option
# rsync -vtr -@3600 --times --progress /media/beffroi/Backup\ Elements/Backup/ /media/beffroi/HDD\ STOCKAGE/
from sys import platform
if platform == "linux" or platform == "linux2":
     dateformat='-t{year:02d}{month:02d}{day:02d}{hour:02d}{minute:02d}.{second:02d}'
#     smalldate="%m%d%H%M.%S"
#     smallyear=
elif platform == "darwin":
    dateformat=""
# elif platform == "win32":
#     sys.exit("Not supported for now")

# import pathlib # getting rid of half of os calls in favor a something way more friendly

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
    if not os.path.exists(path):
        raise IOError("  The folder '{}' doesn't exist".format(path))
    for d in imonths:
        dir=os.path.join(path,d)
        if not os.path.exists(dir):
            doMakedir(dir,p.dry)

def maketest(p):
    "Making a bunch of test files in a destination folder"
    dprint("Making test files")

    size=4
    try:
        doMakedir("test",p.dry)
    except:
        pass
    for j in range(size):
        for i in range(12):
            dest="test/file{0:02d}.txt".format(i+12*j)
            r1=doMakeFile(dest,p.dry)
            r2=doChangeTime(dest,datetime.datetime(year=2000+j,month=i+1,day=i+1,hour=0,minute=0,second=0).timetuple(),p.dry)
    dprint("Test file made")

def makeBackup(p):
    "Backup a folder toward a following destination"
    dprint("Starting backup process...")

    if not p.noupdate:
        updateFolder(p.args[0],p.dry)
    args=p.args
    if len(args)<2:
        raise IndexError("Path argument not found")
    listbackup,listcancel=[],[]
    root,dest=args[0].strip(" '"),args[1].strip(" '")

    if dest.startswith(root):
        raise IndexError("Destination path can't be part of the backup path")
    l=os.listdir(root)
    if len(l)==0:
        dprint("SKIPPING: Directory '{}' is empty".format(root))
        return
        
    for f in l:
        f=os.path.join(root,f)
        t=os.path.getmtime(f)
        month=time.strftime("%b",time.gmtime(t))
        nmonth=emonth[month]
        nyear=time.strftime("%Y",time.gmtime(t))
        move,cancel=makeMovecommand(f,dest,nmonth,nyear)
        listcancel+=[cancel]
        listbackup+=[move]
    dprint("Executing subcommands")
    for l in listbackup:
        cancelf = os.path.join(p.cancel,time.strftime("cancel-%d%b%y-%H%M%S.sh",time.gmtime(time.time())))
        doSubprocess(l,p.dry)
        if not p.nobackup:
            with open(cancelf,"w+") as file:
                for line in listcancel:
                    file.write(' '.join(line)+"\n")
            st=os.stat(cancelf)
            os.chmod(cancelf,st.st_mode | 0o111)

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
                updateFolder(os.path.join(root,dir),p.dry)

def updateFolder(dest,dry):
    "Update one folder with the modified date in one of the files"
    # dprint("Updating folder {}".format(dest))
    for root, dirs, files in os.walk(dest,topdown=True):
        if len(files)==0:
            towalk=dirs
        else:
            towalk=files

        for f in towalk:
            filep=os.path.join(root,f)
            return doChangeTime(dest,time.gmtime(os.path.getmtime(filep)),dry)

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
                    # date="{:02d}/{:02d}/20 {}".format(iyear,imonth,itime)
                    des=os.path.join(dest,root,f)
                    dprint("  > Updating {} with date {}".format(f,date))
                    doChangeTime(f,datetime.datetime(year=iyear,month=imonth,time=itime),p.dry)
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

def makeMovecommand(file,dest,nmonth,nyear):
    "Make a move command, don't actually execute it. Return a list for subprocess."
    fy=os.path.join(dest,nyear)

    destmonth=os.path.join(fy,monthname(nmonth,months[nmonth]))

    if not os.path.exists(fy):
        dprint(" > Destination year doesn't exists...making directory ({})".format(fy))
        doMakedir(fy,p.dry)
    if not os.path.exists(destmonth):
        dprint("  > Dest month doesn't exists...making directory ({})".format(destmonth))
        doMakedir(destmonth,p.dry)
    yearupdate.add(nyear)
    pathdest=finddest(destmonth,os.path.basename(file))

    return ["mv","-n",file,pathdest],["mv","-n",pathdest.replace(' ','\ '),file.replace(" ",'\ ')]

def doSubprocess(listargs,dry=False):
    "Call a subprocess if not dry, and print it if verbose"
    if not dry:
        r=subprocess.call(listargs)
        dprint(" $ "+" ".join(listargs))
    else:
        r=0
        dprint(" # "+" ".join(listargs))
    return r

def doMakedir(dir,dry):
    "Make a directory if not dry"
    dprint(" {} Making directory '{}'".format(dryme(dry),dir))

    r=0
    if not dry:
        r=os.mkdir(dir)

def doChangeTime(file,date,dry):
    "Change the modification time of a file"
    dprint("  {} Changing time of {} with {}".format(dryme(dry),file,time.strftime("%d %b %y - %H:%M:%S",date)))

    modTime = time.mktime(date)
    # print(type(date),type(modTime))
    if not dry:
        os.utime(file, (modTime, modTime))

def doMakeFile(dest,dry):
    dprint("  {} Making file {}".format(dryme(dry),dest))
    with open(dest,"w+") as f:
        pass
    return 0

def dryme(dry):
    if dry:
        return '#'
    return '$'

commands={"make":makeFolders,"backup":makeBackup,"test":maketest,"update":updateFolders,"init":initFiles}

parser = argparse.ArgumentParser(description='Make backup folders.')
parser.add_argument('command',help='Command from list',choices=list(commands.keys()))
parser.add_argument('args',nargs='*',help='Arguments')
parser.add_argument('--verbose',action="store_true",default=True)
parser.add_argument("--quiet",action="store_false",dest="verbose")
parser.add_argument("--recursive",action="store_true",default=False)
parser.add_argument("--noupdate",action="store_true",default=False)
parser.add_argument("--nobackup",action="store_true",default=False)
parser.add_argument("--dry",action="store_true",default=False)
parser.add_argument("--time",default="10:10:10")
parser.add_argument("--cancel", default=".")

# parser.add_argument("--months",default([1,2,3,4,5,6,7,8,9,10,11,12]))
parser.add_argument("--year",default=2019,type=int)

yearupdate=set()
if __name__ == '__main__':
    if len(sys.argv)<2:
        print("Interactive mode engaged")
        def getmefolder(message):
            while 1:
                try:
                    dest=input(message)
                    if dest=="q":
                        sys.exit("...quitting")
                    rf=dest.find("'")
                    if rf>0:
                        dest=dest[rf:dest.rfind("'")]
                    if not os.path.exists(dest):
                        print("{} is not a correct path".format(dest))
                    else:
                        return dest
                except EOFError:
                    sys.exit("...exiting")
                except KeyboardInterrupt:
                    sys.exit("...exiting")
                except IndexError:
                    print("Invalid path")
        while 1:
            origin=getmefolder(" > Type ORIGIN for folders and files : ")
            dest=getmefolder(" > Type DESTINATION for backing them up : ")
            p=parser.parse_args(["backup",origin,dest])
    else:
        p=parser.parse_args()

    errors=0
    if p.verbose:
        def dprint(text):
            print(text)
    try:
        commands[p.command](p)
    except IOError as e:
        errors+=1
        print("ERROR: {}".format(e))
    except IndexError as e:
        errors+=1
        print("ERROR: {}".format(e))
    if errors:
        dprint("Program exited with errors")
    else:
        dprint("Program exited sucessfully")
