#!/usr/bin/python
# obexstress.py v0.1
# ^_^

import lightblue
import StringIO
import sys
import os

if len(sys.argv)!=3:
	print "\n script for testing remote OBEX service for some potential vulnerabilities.\n"
	print "  + tests available commands on remote device, may find directory transversing"
	print "  + tests if some characters in file name can cause a DoS"
	print "  + tests if long file name can cause a DoS"
	print "\n usage: obexstress.py BD_ADDR CHANNEL\n"
	print " ^_^\n"
	sys.exit()

bdaddr = sys.argv[1]
channel = int(sys.argv[2])
test_name = 'AhgA7J892J27H218H'

f = file(test_name, "w")
f.write("test")
f.close

client = lightblue.obex.OBEXClient(bdaddr, channel)

def obex_capab():
	client.connect()
	
	print "\n! NOTE, not all remote OBEX services returns adequate responces and sometimes OK recieved for directory transversing test may be falce positive.\n"

	print "> ls"
	dirlist = StringIO.StringIO()
	ans = client.get({"type": "x-obex/folder-listing"}, dirlist)
	print ans
	if ans.code == lightblue.obex.OK:
		print dirlist.getvalue()

	print "> cd .."
	print client.setpath({},cdtoparent=True)

	print "> ls"
	dirlist = StringIO.StringIO()
	ans = client.get({"type": "x-obex/folder-listing"}, dirlist)
	print ans
	if ans.code == lightblue.obex.OK:
		print dirlist.getvalue()

	print "> cd ../"
	print client.setpath({"name": "../../../"})

	print "> ls"
	dirlist = StringIO.StringIO()
	ans = client.get({"type": "x-obex/folder-listing"}, dirlist)
	print ans
	if ans.code == lightblue.obex.OK:
		print dirlist.getvalue()

	print "> cd %s" % test_name
	print client.setpath({"name": test_name})

	print "> mkdir %s" % test_name
	print client.setpath({"name": test_name}, createdirs=True)

	print "> cd %s" % test_name
	print client.setpath({"name": test_name})

	print "> rmdir %s" % test_name
	print client.delete({"name": test_name})

	print "> put %s" % test_name
	print client.put({"name": test_name},file(test_name, 'rb'))

	print "> get %s" % test_name
	f = file(test_name,"wb")
	print client.get({"name": test_name},f)
	f.close

	print "> rm %s" % test_name
	print client.delete({"name": test_name})

	print "> put ../../../../../%s" % test_name
	print client.put({"name": "../../../../../"+test_name},file(test_name, 'rb'))

	client.disconnect()

def send_malf_name(c):

	namestr = [" ", chr(9), ':', '/','?',"\\",\
	"!\"#$%&\'()*+,-", "@.`;<=>[]^_{|}~", \
	'qwertyuiopasdfghjklzxcvbnm0123456789QWERTYUIOPASDFGHJKLZXCVBNM']

	if c == 99:
		n = raw_input("> enter decimal ASCII character code: ")
		if n.isdigit():
			name = chr(int(n))
		else:
			print "> wrong!"
			return
	else:
		name = namestr[c]

	client.connect()

	print "> sending file with name \'%s\', " % name,
	if len(name)==1: print "(ascii code = %s), " % ord(name),
	print "length = %d" % len(name)
	print client.put({"name": name}, file(test_name, 'rb'))
	client.disconnect()

def send_long_name():

	n = raw_input("> enter name length (e.g. 257): ")
	if n.isdigit():
		length = int(n)
	else:
		print "> wrong!"
		return

	client.connect()

	print "> sending file with %d A characters in name', " % length,
	print "length = %d" % length
	print client.put({"name": 'A'*length}, file(test_name, 'rb'))
	client.disconnect()

# menu
while True:
	print "\n\
    [o] OBEX commands/transversing test    [l] name length test\n\
    \n\
    [m] malformed name test \n\
    \n\
	[1] SPACE (0x20)  [4] / (0x2F)  [7] @.`;<=>[]^_{|}~  \n\
	[2] TAB (0x09)    [5] ? (0x3F)  [8] !\"#$%&\'()*+,- \n\
	[3] : (0x3A)      [6] \\ (0x5C)  [9] alphaALPHAnumeric  \n"

	n = raw_input("> choise (x for exit): ")
	if n=="m":
		send_malf_name(99)
	elif n.isdigit():
	    if int(n) in range(0,10):
		    send_malf_name(int(n)-1)
	    else: print "wrong choice"
	elif n=="o":
		obex_capab()
	elif n=="l":
		send_long_name()
	elif n == 'x':
		os.remove(test_name)
		sys.exit()