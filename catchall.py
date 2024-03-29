#!/usr/bin/env python3
import random
import sys
import csv
import subprocess
import os
import time
from shutil import copyfile
import configparser


TESTMODE = False  # mainly prevents the writing of postfix config
basedir = "/etc/catchall/"
savefile = basedir + "save.csv"
backupdir = basedir + "backup/"
mapfile = "/etc/postfix/virtual"
configfile = basedir + "config"
domains = []
mainaddress = ""
pre_defs = []  # pre defined prefixes (from config), not saved in 'save.csv'
pre_defs_avail = False


def main():
    init()

    if len(sys.argv) > 1:
        if sys.argv[1] == "-a":

            mod_line(sys.argv[2].lower(), generate_prefix(), True, get_mail_addr())
            generate_postfix_config()

        elif sys.argv[1] == "-l" and len(sys.argv) >= 3:
            lookup(sys.argv[2].lower())

        elif sys.argv[1] == "-r":
            mod_line(sys.argv[2].lower(), generate_prefix, False, get_mail_addr())
            generate_postfix_config()

        elif sys.argv[1] == "-l":
            listall()

        elif sys.argv[1] == "-b":
            backup_save()

        elif sys.argv[1] == "-v":
            print("catchall version 0.13")
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
    global pre_defs_avail
    config_p = configparser.ConfigParser()
    config_p.read(configfile)

    if ('main' not in config_p):
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

    pre_def_tmp = config_p['main']['pre_def']
    if len(pre_def_tmp) > 0:
        pre_defs_avail = True

    pre_def = pre_def_tmp.split(',')
    for p in pre_def:
        pre_defs.append(p.split(':'))

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
    response = input("Name already in database: " + line[0] + " - " + line[1] + line[2] + ", replace?\n[yes/NO] ")
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


def generate_postfix_config():
    lines = read_file()
    out = ""

    # append the predefinded prefixes (because they are not contained in the savefile)
    if pre_defs_avail:
        for p in pre_defs:
            # email = p[1].split('@')
            # pref = p[0]
            # tmp =  [p[0], email[0], "@"+email[1]]
            # tmp =  [p[0], p[1]]
            out += p[1] + ' ' + mainaddress + "\n"

    for row in lines:
        out += row[1] + row[2] + ' ' + mainaddress + "\n"

    if not TESTMODE:
        config = open(mapfile, 'w')
        config.write(out)
        config.close()

        print("Mapping postfix file")
        output = subprocess.check_output(["postmap", mapfile])
        print(output)
        print("reloading postfix server")
        output = subprocess.check_output(["/etc/init.d/postfix", "reload"])
    else:
        print("--TESTMODE--")
        print(out)


def lookup(name):
    lines = read_file()
    search_for = name.split("@")  # if array has 2 parts, then it is a reverse lookup (prefix given)

    # append the predefinded prefixes (because they are not contained in the savefile)
    if pre_defs_avail:
        for p in pre_defs:
            # email = p[1].split('@')
            # pref = p[0]
            # tmp =  [p[0], email[0], "@"+email[1]]
            # lines.append(p[0] + p[1])
            tmp = [p[0], p[1]]
            lines.append(tmp)

    if len(search_for) == 1:  # name given
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


def generate_prefix():
    lines = read_file()

    prefixes = []
    for l in lines:
        prefixes.append(l[1])

    test = get_random()  # generate prefixes until an unused prefix is found
    while test in prefixes:
        test = get_random()

    return test


def listall():
    result = []
    result.append(['Name', 'email address'])
    result.append(["-------", "----------------"])
    lines = read_file()

    # append the predefinded prefixes (because they are not contained in the savefile)
    if pre_defs_avail:
        for p in pre_defs:
            # email = p[1].split('@')
            # pref = p[0]
            # tmp =  [p[0], email[0], "@"+email[1]]
            # lines.append(p[0] + p[1])
            tmp = [p[0], p[1]]
            result.append(tmp)

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
    print("""Usage:
             -a [Name] [mail_addr]: add an entry
             -r [Name] [mail_addr]: remove an entry
             -l [Name]            : lookup the available virtual addresses of a given name
             -l [virtual address] : reverse lookup the owner of this virtual address
             -l                   : list all current active virtual addresses
             -b                   : backup the savefile
             -v                   : print version

                if [mail_addr] not given, default is used

             mail_addr (if config readable and addresses set):""")

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
