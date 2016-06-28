#!/usr/bin/python 
# from http://www.optixx.org
#

import sys
import re
import os
import time

if len(sys.argv)<=2:
    print "%s <dev> <bdaddr>" % sys.argv[0]
    sys.exit(-1)

dev   = sys.argv[1]
baddr = sys.argv[2].upper().split(":")

if not re.compile("^hci[\d]$").search(dev):
    print "%s <dev> <bdaddr>" % sys.argv[0]
    sys.exit(-1)
for i in baddr:
    try:
        x = int(i,16)
    except:
        print "%s <dev> <bdaddr>" % sys.argv[0]
        sys.exit(-1)


if len(baddr)!=6:
    print "%s <dev> <bdaddr>" % sys.argv[0]
    sys.exit(-1)

cmd = "./bccmd  -d %s psset -r bdaddr 0x%s 0x%s 0x%s 0x%s 0x%s 0x%s 0x%s 0x%s" % (
                dev,
                baddr[3],
                "00",
                baddr[5],
                baddr[4],
                baddr[2],
                "00",
                baddr[1],
                baddr[0])
print "Exec '%s'" % cmd
os.system(cmd)
time.sleep(3)
os.system("hciconfig %s"  %dev)


