#!/bin/python
import random
import sys
import csv
import subprocess

def main () :
    if len(sys.argv) > 1:
        if sys.argv[1] == "-a":
            mod_line(sys.argv[2], get_random(), True, get_mail_addr())
            generate_postfix_config()
        elif sys.argv[1] == "-l":
            res = lookup(sys.argv[2])
            print ("results for \"" + sys.argv[2] + "\":")
            for r in res:
                print("\t" + r)
                
        elif sys.argv[1] == "-r":
            mod_line(sys.argv[2], get_random(), False, get_mail_addr())
            generate_postfix_config()
    else:
        print_usage()

def get_mail_addr():
    if len(sys.argv) > 3:
        if sys.argv[3] == "0":
            return "@acknexster.de"
        elif sys.argv[3] == "1":
            return "@nope.run"
        elif sys.argv[3] == "2":
            return "@leanderseidlitz.com"
    else:
        return "@acknexster.de"
        
def mod_line (name, pref, add_Entry, mail_addr) :
    #get current file
    save_file = open("save.csv", 'r')
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
    save_file = open("save.csv", 'w')
    w = csv.writer(save_file, delimiter=',', quotechar='|')
    
    for line in lines:
        if line[0] == name and line[2] == mail_addr:
            #user added first time or getting removed,
            #in all other cases, get user confirmation first
            if not was_in or not add_Entry or user_confirm_replace(line):
                line[1] = pref
            if add_Entry:
                print(line)
                w.writerow(line)
        else:
            w.writerow(line)    

    save_file.flush()
    save_file.close()

def user_confirm_replace(line):
    response = input("Name already in database: "+line[0]+" - "+line[1]+", replace?\n[yes/NO] ")
    if response == "yes":
        return True
    else:
        return False
    
def print_file () :
    save_file = open("save.csv", 'r')
    save = csv.reader(save_file, delimiter=',', quotechar='|')
    for row in save:
        print  (row)
    save_file.close()

    
def generate_postfix_config () :
    save_file = open("save.csv", 'r')
    save = csv.reader(save_file, delimiter=',', quotechar='|')
    out = ""
    for row in save:
        out += row[1]+row[2]+' '+"leanseidl@gmail.com\n"
    print (out)
    save_file.close()

    config = open("/etc/postfix/virtual", 'w')
    #config = open("virtual", 'w')
    config.write(out)
    config.close()

    print("Mapping postfix file")
    output = subprocess.check_output(["postmap", "/etc/postfix/virtual"]);
    print(output)
    print("reloading postfix server")
    output = subprocess.check_output(["/etc/init.d/postfix", "reload"]);
    

def lookup (name) :
    result = []
    lines = read_file()
    for l in lines:
        if l[0] == name:
            result.append (l[1]+l[2])

    if len(result) == 0:
        return "No address for name"
    else:
        return result
        
    

def get_random () :
    ran = random.getrandbits(32)
    return format(ran, 'x')

def read_file () :
    save_file = open("save.csv", 'r')
    r = csv.reader(save_file, delimiter=',',quotechar='|')
    lines = list(r)
    save_file.close()
    return lines

def print_usage ():
    print ("Usage:")
    print ("-a [Name] [mail_addr]: add an entry")
    print ("-r [Name] [mail_addr]: remove an entry")
    print ("-l [Name] [mail_addr]: lookup the prefix of a given name")
    print ("mail addr:")
    print ("\t\t 0\t @acknexster.de \t [default]")
    print ("\t\t 1\t @nope.run")
    print ("\t\t 2\t @leanderseidlitz.com")

if __name__ == "__main__":
        main()
