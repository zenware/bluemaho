#!/usr/bin/python
#
# bluetracker.py v0.2
# script for tracking link quality and rssi (recieved signal strength) for specified remote bluetooth enabled device.
#    ideal link quality value is 255 and rssi is 0.
# ^_^

import sys, time, subprocess

def bttrack(adr, dev, delay):
	error_count = 0
	cmd_cc = "hcitool -i %s cc %s" % ( dev, adr )
	cmd_lq = "hcitool -i %s lq %s" % ( dev, adr )
	cmd_rssi = "hcitool -i %s rssi %s" % ( dev, adr )

	while 1:
		out = subprocess.Popen(cmd_cc.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
		time.sleep(1)
		if len(out[1]):
			print "can\'t create connection"
			time.sleep(1)
			error_count += 1
			if error_count == 5:
				print "exiting.."
				return 1
		else:
			while 1:
				out = subprocess.Popen(cmd_lq.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
				if len(out[1]): break
				else: print '%s link quality: %s,' % ( adr, out[0].split()[2]),	
				
				out = subprocess.Popen(cmd_rssi.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
				if len(out[1]): break
				else: print 'rssi: %s' % (out[0].split()[3])
				
				time.sleep(delay)

if len(sys.argv) != 4:
	print "\n\t bluetracker.py <hciN> <bdaddr> <delay in s, default=0.2>\n"
else:
	# get original local name and mode
	orig_auth = False
	cmd = "hciconfig -a %s" % (sys.argv[1])
	cmd_out = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE).communicate()
	if cmd_out[0]:
		a = cmd_out[0].split('\n\t')
		for b in a:
			if "AUTH" in b:
				orig_auth = True
				cmd = "hciconfig -a %s noauth" % (hci_dev)
				subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
				
	bttrack(sys.argv[2], sys.argv[1], float(sys.argv[3]))
	
	if orig_auth == True:
		cmd = "hciconfig -a %s auth" % (hci_dev)
		subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()