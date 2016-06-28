#!/bin/sh
#script for building stuff used by BlueMaho
#

echo -e "\n chmod +x bluemaho.py"
chmod +x ../bluemaho.py

echo -e "\nTrying to build tools..."
echo -e "\ngoing ../tools"

cd ../tools

echo -e "\n chmod +x getmaxlocaldevinfo.sh"
chmod +x getmaxlocaldevinfo.sh

echo -e "\n chmod +x obexstress.py"
chmod +x obexstress.py

echo -e "\n[+] Building atshell.c by Bastian Ballmann (modified attest.c by Marcel Holtmann)"
gcc -lbluetooth -lreadline sources/atshell.c -o atshell

echo -e "\n[+] Building bccmd by Marcel Holtmann"
cd sources/bccmd/
gcc -lusb -lbluetooth csr.c csr_3wire.c csr_bcsp.c csr_h4.c csr_hci.c csr_usb.c ubcsp.c bccmd.c -o bccmd
mv bccmd ../..
cd ../..

echo -e "\n[+] Building bdaddr.c by Marcel Holtmann"
gcc -lbluetooth sources/bdaddr.c -o bdaddr

echo -e "\n[+] Building psm_scan and rfcomm_scan from bt_audit-0.1.1 by Collin R. Mulliner"
cd sources/bt_audit-0.1.1/src/
make
mv psm_scan ../../..
mv rfcomm_scan ../../..
cd ../../..

echo -e "\n[+] Building BSS (Bluetooth Stack Smasher) v0.8 by Pierre Betouin"
cd sources/bss-0.8/
make
mv  bss ../..
cp -R replay_packet ../..
cd ../..

echo -e "\n[+] Building btftp v0.1 by Marcel Holtmann"
cd sources/btftp-0.1/
make
mv btftp ../..
cd ../..

echo -e "\n[+] Building btobex v0.1 by Marcel Holtmann"
cd sources/btobex-0.1/
make
mv btobex ../..
cd ../..

echo -e "\n[+] Building carwhisperer v0.2 by Martin Herfurt"
cd sources/carwhisperer-0.2/
gcc -lbluetooth carwhisperer.c -o carwhisperer
mv carwhisperer ../..
cd ../..

echo -e "\n[+] Building L2CAP packetgenerator by Bastian Ballmann"
cd sources/
gcc -lbluetooth l2cap-packet.c -o l2cap-packet
mv l2cap-packet ..
cd ..

echo -e "\n[+] Building redfang v2.50 by Ollie Whitehouse"
cd sources/redfang-2.50/
make
mv fang ../../redfang
cd ../..

echo -e "\n[+] Building ussp-push v0.10 by Davide Libenzi"
cd sources/ussp-push-0.10/
make
mv ussp-push ../..
cd ../..

echo -e "\nTools building complete.\n"

echo -e "\nTrying to build exploits..."
echo -e "\ngoing ../exploits"




cd ../exploits

echo -e "\n[+] Building Bluebugger v0.1 by Martin J. Muench"
cd sources/bluebugger-0.1/
make
mv bluebugger ../..
cd ../..

echo -e "\n[+] Building bluePIMp by Kevin Finisterre"
cd sources/bluepimp/
make
mv ussp-push ../../bluepimp
cd ../..

echo -e "\n[+] Building BlueZ hcidump v1.29 DoS PoC by Pierre Betouin"
cd sources/
gcc -lbluetooth bluez_hcidump_v129_dos.c -o bluez_hcidump_v129_dos
mv bluez_hcidump_v129_dos ..
cd ..

echo -e "\n[+] Building helomoto by Adam Laurie"
cd sources/helomoto/
make
mv helomoto ../..
cd ../..

echo -e "\n[+] Building hidattack v0.1 by Collin R. Mulliner"
cd sources/hidattack-0.1
make
mv  hidattack ../..
cp ha.inp ../../hidattack.inp
cd ../..

echo -e "\n[+] Building Nokia N70 l2cap packet DoS PoC Pierre Betouin"
cd sources/
gcc -lbluetooth nokiaN70_l2cap_packet_dos.c -o nokiaN70_l2cap_packet_dos
mv nokiaN70_l2cap_packet_dos ..
cd ..

echo -e "\n[+] Building Sony-Ericsson reset display PoC by Pierre Betouin"
cd sources/
gcc -lbluetooth sonyericsson_reset_display.c -o sonyericsson_reset_display
mv sonyericsson_reset_display ..
cd ..

echo -e "\n chmod +x opush_abuse.sh"
chmod +x ../opush_abuse.sh

echo -e "\nExploits building complete.\n"

echo -e "\nBuilding complete! Maho!\n"