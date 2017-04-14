# !/usr/bin/python3
import random
import sys
import csv
import subprocess
import os
import time
from shutil import copyfile
import configparser

TESTMODE = True  # mainly prevents the writing of postfix config
basedir = "/etc/catchall/"
savefile = basedir + "save.csv"
backupdir = basedir + "backup/"
mapfile = "/etc/postfix/virtual"
configfile = basedir + "config"
domains = []
mainaddress = ""


def main():
    init()

    if len(sys.argv) > 1:
        if sys.argv[1] == "-a":
            mod_line(sys.argv[2].lower(), get_random(), True, get_mail_addr())
            generate_postfix_config()

        elif sys.argv[1] == "-l" and len(sys.argv) >= 3:
            lookup(sys.argv[2].lower())

        elif sys.argv[1] == "-r":
            mod_line(sys.argv[2].lower(), get_random(), False, get_mail_addr())
            generate_postfix_config()

        elif sys.argv[1] == "-l":
            listall()

        elif sys.argv[1] == "-b":
            backup_save()

        elif sys.argv[1] == "-v":
            print("catchall version 0.11")
    else:
        print_usage()


def init():
    save_dir = os.path.dirname(basedir)
    if not os.path.exists(save_dir):
        print("base directory missing: " + basedir)
        exit(1)
    backup = os.path.dirname(backupdir)
    if not os.path.exists(backup):
        print("backup directory missing: " + backupdir)
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
        print("config file missing / damages (make sure it begins with '[main]'!")
        exit(1)

    if (len(config_p['main']['domains']) == 0):
        print("no domains [domains] set!")
        exit(1)

    if (len(config_p['main']['mainaddr']) == 0):
        print("Main mail address [mainaddr] not set!")
        exit(1)

    domains_tmp = config_p['main']['domains']
    domains = domains_tmp.split(',')

    mainaddress = config_p['main']['mainaddr']


def get_mail_addr():
    if len(sys.argv) <= 3:
        return domains[0]
    else:
        addr = int(sys.argv[3])
        if (addr > len(domains)):
            return domains[0]  # return default address
        else:
            return domains[addr]


def mod_line(name, pref, add_Entry, mail_addr):
    # get current file
    save_file = open(savefile, 'r')
    r = csv.reader(save_file, delimiter=',', quotechar='|')
    lines = list(r)
    was_in = False
    save_file.close()
    pref_tmp = 0  # used for output and used to check, if removal was necessary

    for line in lines:
        if line[0] == name and line[2] == mail_addr:
            was_in = True
            pref_tmp = line[1]
    if not was_in:
        lines.append([name, pref, mail_addr])

    # write the updated file
    save_file = open(savefile, 'w')
    w = csv.writer(save_file, delimiter=',', quotechar='|')

    for line in lines:
        if line[0] == name and line[2] == mail_addr:
            # user added first time or getting removed,
            # in all other cases, get user confirmation first
            if not was_in or not add_Entry or user_confirm_replace(line):
                line[1] = pref
            if add_Entry:
                w.writerow(line)
        else:
            w.writerow(line)

    save_file.flush()
    save_file.close()

    if add_Entry:  # modified
        print("\n\nnew / modified / untouched entry:")
        for l in lines:  # print the updated entry
            if l[0] == name and l[2] == mail_addr:
                print_line([l[0], l[1] + l[2]])
    else:  # removed
        if not pref_tmp == 0:
            print("removed virtual mapping of '" + name + "' with '" + pref_tmp + mail_addr + "'")
        else:
            print("'" + name + "' in combination with '" + mail_addr + "' had no mapping.")


def user_confirm_replace(line):
    response = input("Name already in database: " + line[0] + " - " + line[1] + ", replace?\n[yes/NO] ")
    if response == "yes":
        return True
    else:
        return False


def backup_save():
    localtime = time.localtime()
    timeString = time.strftime("%Y%m%d%H%M%S", localtime)
    backup_file_name = backupdir + timeString + ".csv.bkp"
    print("saving savefile to: " + backup_file_name)
    copyfile(savefile, backup_file_name)


def print_file():
    save_file = open(savefile, 'r')
    save = csv.reader(save_file, delimiter=',', quotechar='|')
    for row in save:
        print(row)
    save_file.close()


def generate_postfix_config():
    save_file = open(savefile, 'r')
    save = csv.reader(save_file, delimiter=',', quotechar='|')
    out = ""
    for row in save:
        out += row[1] + row[2] + ' ' + mainaddress + "\n"
    save_file.close()

    if not TESTMODE:
        config = open(mapfile, 'w')
        config.write(out)
        config.close()

        print("Mapping postfix file")
        output = subprocess.check_output(["postmap", mapfile]);
        print(output)
        print("reloading postfix server")
        output = subprocess.check_output(["/etc/init.d/postfix", "reload"]);
    else:
        print("--TESTMODE--")
        print(out)


def lookup(name):
    lines = read_file()
    search_for = name.split("@")  # if array has 2 parts, then it is a reverse lookup (prefix given)

    if len(search_for) == 1:  # name or prefix given
        result = []
        for l in lines:
            if l[0] == name:
                result.append([l[0], l[1] + l[2]])
        if len(result) == 0:
            print("No address for name / prefix")
        else:
            print("results for '" + name + "':")
            for l in result:
                print_line(l)

    elif len(search_for) == 2:  # email_address given => reverse lookup
        result = ""
        for l in lines:
            if l[1] == search_for[0] and l[2] == ("@" + search_for[1]):
                result += (l[0])
        if len(result) == 0:
            print("This address belongs to nobody")
        else:
            print("This address belongs to: " + result)


def listall():
    result = []
    result.append(['Name', 'email address'])
    result.append(["-------", "----------------"])
    lines = read_file()
    for l in lines:
        result.append([l[0], l[1] + l[2]])

    for l in result:
        print_line(l)


def print_line(l):
    spaces = ' ' * (20 - len(l[0]))
    print(l[0] + spaces + l[1])


def get_random():
    ran = random.getrandbits(32)
    return format(ran, 'x')


def read_file():
    save_file = open(savefile, 'r')
    r = csv.reader(save_file, delimiter=',', quotechar='|')
    lines = list(r)
    save_file.close()
    return lines


def print_usage():
    print("Usage:")
    print("-a [Name] [mail_addr]: add an entry")
    print("-r [Name] [mail_addr]: remove an entry")
    print("-l [Name]            : lookup the available virtual addresses of a given name")
    print("-l [virtual address] : reverse lookup the owner of this virtual address")
    print("-l                   : list all current active virtual addresses")
    print("-b                   : backup the savefile")
    print("-v                   : print version")
    print("\n if [mail_addr] not given, default is used\n")
    print("\nmail_addr (if config readable and addresses set):")
    print(gen_domain_string())


def gen_domain_string():
    result = ""
    i = 0
    for m in domains:
        if i == 0:
            result += "[DEFAULT] "
        else:
            result += "          "

        result += str(i) + " -> " + m + "\n"
        i = i + 1
    return result


if __name__ == "__main__":
    main()
