echo -e "[0] lsusb" | tee $2
lsusb | tee -a $2
echo -e "\n[1] hciconfig -a" | tee -a $2
hciconfig $1 -a | tee -a $2
echo -e "\n[2] hciconfig commands" | tee -a $2
hciconfig $1 commands | tee -a $2
echo -e "\n[3] hciconfig features" | tee -a $2
hciconfig $1 features | tee -a $2
echo -e "\n[4] hciconfig revision" | tee -a $2
hciconfig $1 revision | tee -a $2
echo -e "\n[5] bccmd buildname:" | tee -a $2
tools/bccmd -d $1 buildname | tee -a $2
echo -e "\n[6] bccmd memtypes:" | tee -a $2
tools/bccmd -d $1 memtypes | tee -a $2
echo -e "\n[7] bccmd psread:" | tee -a $2
tools/bccmd -d $1 psread | tee -a $2