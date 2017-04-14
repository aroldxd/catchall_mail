#!/usr/bin/python3
import random
import sys
import csv
import subprocess
import os
import time
from shutil import copyfile
import configparser

TESTMODE = False #mainly prevents the writing of postfix config
basedir="/etc/catchall/"
savefile=basedir+"save.csv"
backupdir=basedir+"backup/"
mapfile="/etc/postfix/virtual"
configfile=basedir+"config"
domains=[]
mainaddress=""

def main () :
    init()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "-a":
            mod_line(sys.argv[2], get_random(), True, get_mail_addr(sys.argv[3]))
            generate_postfix_config()
        elif sys.argv[1] == "-s":
            lookup(sys.argv[2])
                
        elif sys.argv[1] == "-r":
            mod_line(sys.argv[2], get_random(), False, get_mail_addr(sys.argv[3]))
            generate_postfix_config()

        elif sys.argv[1] == "-l":
            listall()

        elif sys.argv[1] == "-b":
            backup_save()
    else:
        print_usage()

def init () :
    save_dir = os.path.dirname(basedir)
    if not os.path.exists(save_dir):
        print("base directory missing: "+basedir)
        exit(1)
    backup = os.path.dirname(backupdir)
    if not os.path.exists(backup):
        print("backup directory missing: "+backupdir)
        exit(1)
    if os.path.isfile(savefile):
        os.utime(savefile, None)
    else:
        open(savefile, 'a').close()
        print("created savefile")

    if os.path.isfile(configfile):
        os.utime(savefile, None)
    else:
        open(configfile, 'a').close()
        print("created configfile")

    readconfig()

def readconfig():
    global domains
    global mainaddress
    config_p = configparser.ConfigParser()
    config_p.read(configfile)
    
    if (not 'main' in config_p):
        print ("config file missing / damages (make sure it begins with '[main]'!")
        exit(1)

    if (len(config_p['main']['domains']) == 0):
        print ("no domains [domains] set!")
        exit(1)

    if (len(config_p['main']['mainaddr']) == 0):
        print ("Main mail address [mainaddr] not set!")
        exit(1)
        
    domains_tmp = config_p['main']['domains']
    domains = domains_tmp.split(',')
    
    mainaddress = config_p['main']['mainaddr']
           

def get_mail_addr(num):
    if len(sys.argv) < 3:
        return domains[0]
    
    addr = int(num)
    if (addr > len(domains)):
        return domains[0] #return default address
    else:
        return domains[addr]
    
def mod_line (name, pref, add_Entry, mail_addr) : 
    #get current file
    save_file = open(savefile, 'r')
    r = csv.reader(save_file, delimiter=',',quotechar='|')
    lines = list(r)
    was_in = False
    save_file.close()

    for line in lines:
        if line[0] == name and line[2] == mail_addr:
            was_in = True
    if not was_in:
        lines.append ([name, pref, mail_addr])
            
    #write the updated file
    save_file = open(savefile, 'w')
    w = csv.writer(save_file, delimiter=',', quotechar='|')
    
    for line in lines:
        if line[0] == name and line[2] == mail_addr:
            #user added first time or getting removed,
            #in all other cases, get user confirmation first
            if not was_in or not add_Entry or user_confirm_replace(line):
                line[1] = pref
            if add_Entry:
                w.writerow(line)
        else:
            w.writerow(line)
            
    save_file.flush()
    save_file.close()

    print ("\n\nnew / modified entry:")
    for l in lines: #print the updated entry
        if l[0] == name and l[2] == mail_addr:
            print_line ([l[0], l[1]+l[2]])

        
def user_confirm_replace(line):
    response = input("Name already in database: "+line[0]+" - "+line[1]+", replace?\n[yes/NO] ")
    if response == "yes":
        return True
    else:
        return False

def backup_save () :
    localtime   = time.localtime()
    timeString  = time.strftime("%Y%m%d%H%M%S", localtime)
    backup_file_name = backupdir+timeString+".csv.bkp"
    print ("saving savefile to: "+backup_file_name)
    copyfile(savefile, backup_file_name)
    
    
def print_file () :
    save_file = open(savefile, 'r')
    save = csv.reader(save_file, delimiter=',', quotechar='|')
    for row in save:
        print  (row)
    save_file.close()

    
def generate_postfix_config () :    
    save_file = open(savefile, 'r')
    save = csv.reader(save_file, delimiter=',', quotechar='|')
    out = ""
    for row in save:
        out += row[1]+row[2]+' '+"leanseidl@gmail.com\n"
    save_file.close()

    if not TESTMODE:
        config = open(mapfile, 'w')
    else:
        config = open("virtual", 'w')

    config.write(out)
    config.close()

    if not TESTMODE:
        print("Mapping postfix file")
        output = subprocess.check_output(["postmap", mapfile]);
        print(output)
        print("reloading postfix server")
        output = subprocess.check_output(["/etc/init.d/postfix", "reload"]);
    

def lookup (name) :
    result = []
    lines = read_file()
    for l in lines:
        if l[0] == name:
            result.append ([l[0], l[1]+l[2]])

    if len(result) == 0:
        print ("No address for name")
    else:
        for l in result:
            print_line(l)

def listall () :
    result = []
    result.append (['Name', 'email Adresse'])
    result.append (["-------", "----------------"])
    lines = read_file()
    for l in lines:
        result.append([l[0], l[1]+l[2]])

    for l in result:
        print_line(l)

def print_line(l) :
    spaces = ' ' * (20 - len(l[0]))
    print (l[0] + spaces + l[1])

        
def get_random () :
    ran = random.getrandbits(32)
    return format(ran, 'x')

def read_file () :
    save_file = open(savefile, 'r')
    r = csv.reader(save_file, delimiter=',',quotechar='|')
    lines = list(r)
    save_file.close()
    return lines

def print_usage ():
    print ("Usage:")
    print ("-a [Name] [mail_addr]: add an entry")
    print ("-r [Name] [mail_addr]: remove an entry")
    print ("-s [Name] [mail_addr]: (search) lookup the prefix of a given name")
    print ("-l                   : list all current members of the savefile")
    print ("-b                   : backup the savefile")
    print ("\nmail addr (if config readable and addresses set):")
    print (gen_domain_string())

def gen_domain_string():
    result = ""
    i = 0
    for m in domains:
        result += "\t"+str(i)+"\t"+m
        if i == 0:
            result += "\t[DEFAULT]"
        result += "\n"
        i=i+1
    return result
    
if __name__ == "__main__":
        main()
