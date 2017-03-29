#!/bin/python
import random
import sys
import csv

def main () :
    add_line(sys.argv[1], get_random())
    generate_postfix_config()

def add_line (name, pref) :
    #get current file
    save_file = open("save.csv", 'rb')
    r = csv.reader(save_file, delimiter=' ',quotechar='|')
    lines = list(r)
    was_in = False

    #replace / add
    for line in lines:
        if line[0] == name:
            line[1] = pref
            was_in = True

    #re-add entry
    if not was_in:
        lines += [[name, pref]]

    #write the updated file
    save_file.close()
    save_file = open("save.csv", 'wb')
    w = csv.writer(save_file, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    w.writerows(lines)
    save_file.flush()
    save_file.close()

    
def print_file () :
    save_file = open("save.csv", 'rb')
    save = csv.reader(save_file, delimiter=' ', quotechar='|')
    for row in save:
        print ', '.join(row)
    save_file.close()

    
def generate_postfix_config () :
    save_file = open("save.csv", 'rb')
    save = csv.reader(save_file, delimiter=' ', quotechar='|')
    out = ""
    for row in save:
        out += row[1]+"@acknexster.de"+' '+"leanseidl@gmail.com\n"
    print out
    save_file.close()
    

def get_random () :
    ran = random.getrandbits(32)
    return format(ran, 'x')


if __name__ == "__main__":
        main()
