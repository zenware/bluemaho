#!/usr/bin/python

NAME = 'BlueMaho'
VERSION = "v.090330" # YEAR, MONTH, DAY of release
# so, we'll try to use Y:M:D as versioning, 'cos we can display in 6bytes not only version of release but also date -_^
CONFIG_FILENAME = 'config/default.conf'

import os
import subprocess
import sys
from datetime import datetime
from datetime import date
from threading import Thread
from time import sleep

import wx
import wx.grid

#mainframe
ID_MAINFRAME = 777
ID_MF_TOOLBAR_EXIT = 100
ID_MF_TOOLBAR_ABOUT = 101
ID_MF_TOOLBAR_SCAN_START = 102
ID_MF_TOOLBAR_SCAN_STOP = 103
ID_MF_TOOLBAR_LOCATION = 104
ID_MF_TOOLBAR_LOCALDEV = 105
ID_MF_BUTTON_RUNTOOL = 106
ID_MF_CHOICE_EXPLOIT  = 107
ID_MF_CHOICE_TOOL = 108
ID_MF_CHOICE_HCISCANDEV = 109
ID_MF_CHOICE_HCITOOLDEV = 110
ID_MF_CHECKBOX_LOG = 111
ID_MF_CHECKBOX_LOOP = 112
ID_MF_CHECKBOX_ONNEWDEV = 113
ID_MF_CHECKBOX_SDP = 114
ID_MF_CHECKBOX_SOUND = 115
ID_MF_CHECKBOX_TRACKINFO = 116
ID_MF_TOOLBAR_HANDBOOK = 117
ID_MF_TOOLBAR_STAT = 119
ID_MF_TOOLBAR_BLANK = 120

#localdev
ID_LD_BUTTON_CLOSE = 201
ID_LD_BUTTON_CLASS = 202
ID_LD_BUTTON_BDADDR = 203
ID_LD_BUTTON_NAME = 204
ID_LD_BUTTON_REFRESH = 205
ID_LD_BUTTON_SHOWMAXINFO = 206
ID_LD_CHOICE_HCI = 207
ID_LD_CHECKBOX_AUTH = 208
ID_LD_CHECKBOX_ENCRYPT = 209
ID_LD_CHECKBOX_SECMGR = 210
ID_LD_CHECKBOX_VISIBLE = 211

#stat
ID_ST_HOURS_STAT = 301
ID_ST_BUTTON_RUN = 302
ID_ST_BUTTON_CLOSE = 303

EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

class WorkerThread(Thread):
    def __init__(self, window):
        Thread.__init__(self)
        self._want_abort = 0
        self.start()
        
    def run(self):
	    
	    hci_dev = frame_main.HCI_SCAN_DEVICE
	    scan_results = []
	    	    
	    # do scan
	    cmd_scan = defconf.cmd_hcitool_scan.replace('@hci@', hci_dev)
	    cmd_scan_out = subprocess.Popen(cmd_scan.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
	    
	    # parse scan results
	    if len(cmd_scan_out[0]) > 16:
		devices = []
		
		date = str(datetime.now().date())
		time = str(datetime.now().time())[:8]
		
		for record in cmd_scan_out[0].split('\n\n')[1:-1]:
		    device = [date,time,'','','','unknown','unknown','unknown','']
				# 0 date, 1 time, 2 bt_addr, 3 name, 4 device_class+type, 5 device_vendor, 6 chip_manufacturer, 7 lmp_ver, 8 sdp
		    record = record.split('\n')
		    device[2] = record[0][12:29:] #addr
		    
		    # oui search
		    oui_database = open(defconf.file_oui,"r")
		    oui_pat = device[2][:8].replace(':','')
		    for line in oui_database:
			if oui_pat in line: device[5] = line.split('\t')[2].strip() #device_vendor
		    oui_database.close()

		    device[3] = record[1][13:].replace('[cached]','') #name
		    device[4] = record[2][14:].replace("Device conforms to the ","") #class+type
		    if len(record)>3:
			device[6] = record[3][14:] # chip manufacturer
			device[7] = record[4][13:16:] # lmp ver
				
		    devices.append(device)
		
		if defconf.flag_do_sdp: # get SDP info
			for device in devices:
				sdp_services_list = []
				cmd_sdp_browse = '%s %s' % (defconf.cmd_sdp_browse.replace('@hci@', hci_dev), device[2])
				cmd_sdp_browse_output = subprocess.Popen(cmd_sdp_browse.split(), stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
				if cmd_sdp_browse_output[0][0] =='B': # 'Browsing'
					if len(cmd_sdp_browse_output[0])  == 31:
						device[8]  = 'no services found.'
					else:
						try:
							device[8] = cmd_sdp_browse_output[0].split('\n\n') [:-1]
							device[8][0] = device[8][0][31:] # another way to remove first line?
						except:
							device[8]  = 'no services found.'
				else:
					sdp_services_list = ['error']
			else:
				sdp_services_list = ['unknown']
						
		scan_results = devices

	    else:
		    scan_results = 0
		
            if self._want_abort:
                wx.PostEvent(frame_main, ResultEvent(None))
                return

	    wx.PostEvent(frame_main, ResultEvent(scan_results))
	
    def abort(self):
        self._want_abort = 1



class Frame_Main(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, ID_MAINFRAME, "", (0, 0), (404, 522), style=wx.CAPTION | wx.MINIMIZE_BOX)
	
    # INITIALIZE SOME VARIABLES
        self.worker = None
	self.threads = []
	EVT_RESULT(self,self.OnResult) # Set up event handler for any worker thread results
	self.inquiry_running = False
	self.selected_device = 'BT_ADDR'
	self.buffer_onnewdev = []
        self.count = 0
	self.unique_devices_found = 0

  # WINDOW SETTINGS
	if verbose: print "[3] Drawing main window"
	self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
	fontl = wx.Font(defconf.theme_fontsize,wx.TELETYPE,wx.NORMAL,wx.NORMAL,False,u'Arial')
	self.SetIcon(wx.Icon(defconf.theme_ico_main,wx.BITMAP_TYPE_PNG))
	self.SetMinSize((380,522))
	self.SetMaxSize((380,522))
	self.SetPosition((defconf.horizontal_pos, defconf.vertical_pos))
	self.SetLabel(NAME+' @'+defconf.user_location+' ')

  #TOOLBAR
	self.toolbar = self.CreateToolBar()  #style=wx.NO_BORDER | wx.TB_FLAT ?
	self.toolbar.SetToolBitmapSize((24,24))
	self.toolbar.AddSeparator()
	self.toolbar.AddLabelTool(ID_MF_TOOLBAR_SCAN_START, "", wx.Bitmap(defconf.theme_ico_tb_run), shortHelp='start scan')
	self.Bind(wx.EVT_TOOL, self.StartInquiryScan, id=ID_MF_TOOLBAR_SCAN_START)
	self.toolbar.AddLabelTool(ID_MF_TOOLBAR_SCAN_STOP, "", wx.Bitmap(defconf.theme_ico_tb_stop), shortHelp='stop scan')
	self.toolbar.EnableTool(ID_MF_TOOLBAR_SCAN_STOP, False)
	self.toolbar.AddSeparator()
	self.Bind(wx.EVT_TOOL, self.StopInquiryScan, id=ID_MF_TOOLBAR_SCAN_STOP)
	self.toolbar.AddLabelTool(ID_MF_TOOLBAR_LOCATION, "", wx.Bitmap(defconf.theme_ico_tb_location), shortHelp='set your location')
	self.Bind(wx.EVT_TOOL, self.SetLocation, id=ID_MF_TOOLBAR_LOCATION)
	self.toolbar.AddLabelTool(ID_MF_TOOLBAR_LOCALDEV, "", wx.Bitmap(defconf.theme_ico_tb_dev), shortHelp='local HCI devices settings')
	self.Bind(wx.EVT_TOOL, self.DeviceSettings, id=ID_MF_TOOLBAR_LOCALDEV)
	self.toolbar.AddLabelTool(ID_MF_TOOLBAR_HANDBOOK, "", wx.Bitmap(defconf.theme_ico_tb_handbook), shortHelp='handbook')
	self.Bind(wx.EVT_TOOL, self.OnHandbook, id=ID_MF_TOOLBAR_HANDBOOK)

	self.toolbar.AddLabelTool(ID_MF_TOOLBAR_STAT, "", wx.Bitmap(defconf.theme_ico_tb_stat), shortHelp='statistics')
	self.Bind(wx.EVT_TOOL, self.OnStat, id=ID_MF_TOOLBAR_STAT)
	
	self.toolbar.AddSeparator()
	#self.toolbar.AddLabelTool(ID_MF_TOOLBAR_BLANK, "", wx.Bitmap(defconf.theme_ico_tb_blank), shortHelp='')
	#self.toolbar.EnableTool(ID_MF_TOOLBAR_BLANK, False)

	self.toolbar.AddLabelTool(ID_MF_TOOLBAR_ABOUT, "", wx.Bitmap(defconf.theme_ico_tb_about), shortHelp='what\'s that? o_0')
	self.Bind(wx.EVT_TOOL, self.OnAbout, id=ID_MF_TOOLBAR_ABOUT)

	self.toolbar.AddLabelTool(ID_MF_TOOLBAR_EXIT, "", wx.Bitmap(defconf.theme_ico_tb_exit), shortHelp='exit')
	self.Bind(wx.EVT_TOOL, self.OnTimeToQuit, id=ID_MF_TOOLBAR_EXIT)
	self.toolbar.AddSeparator()
	self.toolbar.Realize()

  # PANEL
	panel = wx.Panel(self,  style=wx.NO_BORDER)
	panel.SetBackgroundColour(defconf.theme_bgcolor)
	panel.SetForegroundColour(defconf.theme_fgcolor)
	panel.SetFont(fontl)

  # CHECKBOXES
	# loop scan
	self.checkbox_loopscan = wx.CheckBox(panel, ID_MF_CHECKBOX_LOOP, "loop scan", (280,5), (100,17))
	self.checkbox_loopscan.SetValue(defconf.flag_loop_scan)
	self.checkbox_loopscan.Bind(wx.EVT_CHECKBOX, self.OnCheckLoop, id=ID_MF_CHECKBOX_LOOP)
	
	# sdp discovery
	self.checkbox_sdp = wx.CheckBox(panel,ID_MF_CHECKBOX_SDP,"get SDP info",(280,22),(100,17))
	self.checkbox_sdp.SetValue(defconf.flag_do_sdp)
	self.checkbox_sdp.Bind(wx.EVT_CHECKBOX, self.OnCheckSdp,id=ID_MF_CHECKBOX_SDP)
	
	# onnewdev - execute command if new device found
	self.checkbox_onnewdev = wx.CheckBox(panel,ID_MF_CHECKBOX_ONNEWDEV,"on new dev",(280,39),(100,17))
	self.checkbox_onnewdev.SetValue(defconf.flag_onnewdev)
	self.ReadCmdForOnNewDeviceFound(defconf.file_on_new_dev_found)
	self.checkbox_onnewdev.Bind(wx.EVT_CHECKBOX, self.OnCheckNewDev,id=ID_MF_CHECKBOX_ONNEWDEV)
	
	# log
	self.checkbox_log = wx.CheckBox(panel,ID_MF_CHECKBOX_LOG,"write to log",(280,56),(100,17))
	self.checkbox_log.SetValue(defconf.flag_log)
	self.checkbox_log.Bind(wx.EVT_CHECKBOX, self.OnCheckLog,id=ID_MF_CHECKBOX_LOG)
	
	# play sound if new device found
	self.checkbox_sound = wx.CheckBox(panel,ID_MF_CHECKBOX_SOUND,"play sound",(280,73),(100,17))
	self.sound = wx.Sound(defconf.theme_snd_onnewdev)
	self.checkbox_sound.SetValue(defconf.flag_sound)
	self.checkbox_sound.Bind(wx.EVT_CHECKBOX, self.OnCheckSound,id=ID_MF_CHECKBOX_SOUND)
	
	# show track info
	self.checkbox_trackinfo = wx.CheckBox(panel,ID_MF_CHECKBOX_TRACKINFO,"trackinfo",(280,90),(100,17))
	self.checkbox_trackinfo.SetValue(defconf.flag_trackinfo)
	self.checkbox_trackinfo.Bind(wx.EVT_CHECKBOX, self.OnCheckTrackinfo,id=ID_MF_CHECKBOX_TRACKINFO)

    # LOCAL HCI ADAPTERS CONTROLS
	self.hci_list = ['none']
		
	self.choicer_hci_scan = wx.Choice(panel,ID_MF_CHOICE_HCISCANDEV,wx.Point(285,112), wx.Size(54,20),choices=self.hci_list,style = wx.CB_DROPDOWN)
	self.choicer_hci_scan.Bind(wx.EVT_CHOICE, self.OnChoiseHciScanDevice, id=ID_MF_CHOICE_HCISCANDEV)
	self.choicer_hci_scan.SetSelection(0)
	wx.StaticText(panel,-1,"scan",wx.Point(342,115), wx.Size(54,20))
	
	self.choicer_hci_plug = wx.Choice(panel,ID_MF_CHOICE_HCITOOLDEV,wx.Point(285,137), wx.Size(54,20),choices=self.hci_list)
	self.choicer_hci_plug.Bind(wx.EVT_CHOICE, self.OnChoiseHciPlugDevice, id=ID_MF_CHOICE_HCITOOLDEV)
	self.choicer_hci_plug.SetSelection(0)
	wx.StaticText(panel,-1,"tools",wx.Point(343,140), wx.Size(54,20))
	
	self.HciListRefresh()

    #BOX FOR FOUND DEVICES
	self.monscreen = wx.grid.Grid(panel,-1,wx.Point(6,5),size=(270,152))
	self.monscreen.SetFont(fontl)
	self.monscreen.SetDefaultColSize(1, False)
	self.monscreen.SetDefaultCellFont(wx.Font(defconf.theme_fontsize_dev, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, 0,  "Arial", wx.FONTENCODING_UTF8 ))
	self.monscreen.SetDefaultRowSize(10, True)
	self.monscreen.CreateGrid(0,4)
	self.monscreen.SetSelectionMode(self.monscreen.SelectRows)
	self.monscreen.EnableEditing(False)
	self.monscreen.SetDefaultCellBackgroundColour(defconf.theme_bgcolor_displ)
	self.monscreen.SetCellHighlightPenWidth(0)
	self.monscreen.SetRowLabelSize(0)
	self.monscreen.SetColLabelSize(0)
	self.monscreen.EnableGridLines(False)
	self.monscreen.DisableDragColSize()
	self.monscreen.DisableDragRowSize()
	self.monscreen.SetColSize(0, 50) # last seen
	self.monscreen.SetColSize(1, 115) # bt_addr
	self.monscreen.SetColSize(2, 88) # name
	self.monscreen.SetColSize(3, 1) # device info
	self.monscreen.SetColMinimalAcceptableWidth(1)
	
	img = wx.Image(defconf.theme_img_dborder, wx.BITMAP_TYPE_PNG)
	img_display = wx.StaticBitmap(panel,-1,wx.BitmapFromImage(img),pos=(5,4))

	self.monscreen.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,self.OnSelectDevice)

    #BOX FOR SELECTED DEVICE INFO
	self.selected_dev_info = wx.StaticText(panel, -1,"",wx.Point(7,162), wx.Size(376,155))

    # TOOLS AND EXPLOITS CONTROLS
	self.HCI_SCAN_DEVICE = self.hci_list[0]
	self.HCI_PLUG_DEVICE = self.hci_list[0]
	
	# read exploits list from file
	file = open(defconf.file_exploits_list,'r')
	self.expl = {' select exploit':''}
	for line in file:
		if line[0] !='#':  self.expl[line.split('\t')[0]] = line.split('\t')[1].strip()
	file.close()
	self.expl_list = self.expl.keys()
	self.expl_list.sort()	
	
	#create exploits choicer
	self.exploit_choiser = wx.Choice(panel,ID_MF_CHOICE_EXPLOIT,wx.Point(53,344), wx.Size(190,20),choices=self.expl_list,style = wx.CB_DROPDOWN)
	self.exploit_choiser.Bind(wx.EVT_CHOICE, self.OnExploitChose, id=ID_MF_CHOICE_EXPLOIT)

	#read tools list from file
	file = open(defconf.file_tools_list,'r')
	self.tools = {' select tool':''}
	for line in file:
		if line[0] !='#':  self.tools[line.split('\t')[0]] = line.split('\t')[1].strip()
	file.close()
	self.tools_list = self.tools.keys()
	self.tools_list.sort()	
	
	#create tools choicer
	self.tool_choiser = wx.Choice(panel,ID_MF_CHOICE_TOOL,wx.Point(246,344), wx.Size(130,20),choices=self.tools_list,style = wx.CB_DROPDOWN)
	self.tool_choiser.Bind(wx.EVT_CHOICE, self.OnToolChose, id=ID_MF_CHOICE_TOOL)

	#create run button
	self.run_button = wx.Button(panel,ID_MF_BUTTON_RUNTOOL,"run",wx.Point(340,368), wx.Size(36,20))
	self.run_button.Bind(wx.EVT_BUTTON, self.RunTool,id=ID_MF_BUTTON_RUNTOOL)

	#create 'cmd-line'
	self.cmdline = wx.TextCtrl(panel, -1, "",wx.Point(2,368), wx.Size(336,20))
	
    #LOGGER
	WellcomeMsg = '> '+str(datetime.now())[:-7]+' ' + "bluemaho loaded.\n"
	self.logger = wx.TextCtrl(panel, -1,WellcomeMsg,wx.Point(2,392), wx.Size(374,80),wx.TE_MULTILINE | wx.TE_READONLY)
	self.logger.SetFont(wx.Font(defconf.theme_fontsize_log,wx.TELETYPE,wx.NORMAL,wx.NORMAL,False,u'Arial'))
	

  ################
    
    # GENERAL FUNCTIONS
    
    def HciListRefresh(self):
	pos_hci_t = self.choicer_hci_scan.GetCurrentSelection()
	pos_hci_e = self.choicer_hci_plug.GetCurrentSelection()
	self.hci_list = []

	cmd_hciconfig_out = subprocess.Popen(defconf.cmd_hciconfig,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
	if cmd_hciconfig_out[0]:
		elements = cmd_hciconfig_out[0].split('\n\n')[:-1]
		for element in elements:
			self.hci_list.append(element[:4])
	else:
		self.hci_list = ['none']
	
	self.choicer_hci_scan.Clear()
	self.choicer_hci_scan.AppendItems(self.hci_list)
	self.choicer_hci_scan.SetSelection(pos_hci_t)
	
	self.choicer_hci_plug.Clear()
	self.choicer_hci_plug.AppendItems(self.hci_list)
	self.choicer_hci_plug.SetSelection(pos_hci_e)

    def PrintIntoLogger(self, text):
	text = "> %s %s" % (str(datetime.now().time())[:8], text)
	self.logger.AppendText(text)

    def OnTimeToQuit(self, event):
	self.Destroy()
	
    def OnAbout(self, event):
	frame_about = AboutBout(self,"")
	frame_about.Show(True)	

    def OnHandbook(self, event):
	frame_handbook = Handbook(self,"")
	frame_handbook.Show(True)	

    def OnStat(self, event):
	frame_stat = Stat(self,"")
	frame_stat.Show(True)	

    # PREFERENCES FUNCTIONS

    def SetLocation(self, event):
	    dialog = wx.TextEntryDialog(self, "", "specify your location", defconf.user_location, style=wx.OK|wx.CANCEL)
	    if dialog.ShowModal() == wx.ID_OK:
		    defconf.user_location = dialog.GetValue()
		    self.SetLabel(NAME+' @'+defconf.user_location+' ')
		    self.unique_devices_found = 0
		    self.buffer_onnewdev = []

    def OnCheckSdp(self, event):
	defconf.flag_do_sdp = not defconf.flag_do_sdp

    def OnCheckLoop(self, event):
	defconf.flag_loop_scan = not defconf.flag_loop_scan

    def OnCheckLog(self, event):
	defconf.flag_log = not defconf.flag_log
	
    def OnCheckSound(self, event):
	defconf.flag_sound = not defconf.flag_sound
	
    def OnCheckNewDev(self, event):
	defconf.flag_onnewdev = not defconf.flag_onnewdev
	if defconf.flag_onnewdev: self.ReadCmdForOnNewDeviceFound(defconf.file_on_new_dev_found)

    def ReadCmdForOnNewDeviceFound(self, filename):
	file = open(filename,'r')
	for line in file:
	    if line[0] !='#':  cmd = line.strip()
	file.close()
	return cmd

    def OnNewDevFound(self, dev):
	self.PrintIntoLogger('running command for new device...\n')
	cmd = self.cmd_onnewdev.replace('@bt_addr@', dev)
	cmd = cmd.replace('@hci@', self.HCI_PLUG_DEVICE).replace('@hci_num@',self.HCI_PLUG_DEVICE[3:])
	subprocess.Popen(cmd.split())

    def OnCheckTrackinfo(self, event):
	defconf.flag_trackinfo = not defconf.flag_trackinfo

    def OnChoiseHciScanDevice(self, event):
	self.HCI_SCAN_DEVICE = self.hci_list[self.choicer_hci_scan.GetCurrentSelection()]
	    
    def OnChoiseHciPlugDevice(self, event):
	self.HCI_PLUG_DEVICE = self.hci_list[self.choicer_hci_plug.GetCurrentSelection()]

    def DeviceSettings(self, event):
	frame_local_dev = Frame_LocalDev(self,"")
	frame_local_dev.Reinit()
	frame_local_dev.Show(True)


    # SCAN FUNCTIONS

    def StartInquiryScan(self, event):
	if self.HCI_SCAN_DEVICE != 'none':
		self.monscreen.DeleteRows(0,self.monscreen.GetNumberRows(),True)
		self.toolbar.EnableTool(ID_MF_TOOLBAR_SCAN_START, False)
		self.toolbar.EnableTool(ID_MF_TOOLBAR_SCAN_STOP, True)
		self.RunInquiryScan()
	else:
		self.PrintIntoLogger('can\'t find usable adapter to perform scan!\n')
			
    def RunInquiryScan(self):
	self.inquiry_running = True
	self.selected_dev_info.SetLabel("")
	self.PrintIntoLogger('scaning...\n')
	self.worker = WorkerThread(self)

    def OnResult(self, event):
        if event.data is None:
		self.PrintIntoLogger('scan aborted.\n')
		self.worker = None
        else:
		if event.data == 0:
			self.PrintIntoLogger('no devices found.\n')
			self.monscreen.DeleteRows(0,self.monscreen.GetNumberRows(),True)
		else:
			devices = event.data

			#write to logger
			for dev in devices:
			# 0 date, 1 time, 2 bt_addr, 3 name, 4 device_class+type, 5 device_vendor, 6 chip_manufacturer, 7 lmp_ver, 8 sdp
			        dev[1] = dev[1][:-3]
				if dev[2] not in self.buffer_onnewdev: #is it new device?
				    self.unique_devices_found +=1
				    label = "%s @%s found %s devices" % (NAME, defconf.user_location, self.unique_devices_found)
				    self.SetLabel(label)
				    if defconf.flag_sound:
					self.sound.Play(wx.SOUND_ASYNC)
				    if defconf.flag_onnewdev:
					self.OnNewDevFound(dev[2])
				    self.buffer_onnewdev.append(dev[2])

			   	# sdp
				dev8_temp = []
				
				if dev[8] != '':
					for b in dev[8]:
						stri = ''
						for c in b.split('\n'):
							if 'Name:' in c: stri = c[14:].replace('Bluetooth ','').strip() #garbage 'Bluetooth' before all profile names
							if 'Channel:' in c:
								if stri !='': stri = stri+' (ch:%s)'% (c[13:].strip()) # some Nokia bug :(
							if 'PSM:' in c: stri =  stri+' (PSM:%s)' % (c[9:].strip())
						dev8_temp.append(stri)
						
					dev[8] = dev8_temp
				
					dev[8].sort()
					
					sdp_services_string = ''
					counter2 = 10
					for service in dev[8]:
						if counter2 + len(service)> 62:
							sdp_services_string = sdp_services_string+'\n'
							counter2 = 0
						sdp_services_string = sdp_services_string + service + ', '
						counter2 = counter2 + len(service)
					dev[8]=sdp_services_string[:-2]
				else:
					dev[8] = 'undiscovered'

				msg_to_logger = "found %s %s\ndevice type: %s;\nvendor: %s;\nchip: %s; LMP ver: %s\nservices: %s\n" \
								% (dev[2], dev[3], dev[4], dev[5], dev[6], dev[7],dev[8].replace('\n',''))

				self.PrintIntoLogger(msg_to_logger)

			#if log enabled write to log file
			if defconf.flag_log:
				self.WriteToLog(devices)

			self.ShowInGrid(devices)
	
		self.worker = None
		if defconf.flag_loop_scan:
			if self.inquiry_running: self.RunInquiryScan()
		else:
			self.toolbar.EnableTool(ID_MF_TOOLBAR_SCAN_START, True)
			self.toolbar.EnableTool(ID_MF_TOOLBAR_SCAN_STOP, False)
			self.PrintIntoLogger('scan finished.\n')


    def ShowInGrid(self, devices):
	self.monscreen.DeleteRows(0,self.monscreen.GetNumberRows(),True)
	for dev in devices:
		a = self.monscreen.GetNumberRows()
		self.monscreen.AppendRows(1, True)
		self.monscreen.SetCellValue(a, 0,  '- '+dev[1])  #time
		self.monscreen.SetCellValue(a, 1,  dev[2])  #addr
		self.monscreen.SetCellValue(a, 2,  dev[3])  #name
		
		#tracking stuff
		if defconf.flag_trackinfo:
			times_seen = 0
			names_before = []
			names_before_str = ''
			places_str = ''
			name = ''
			first_seen = 'never before'
			log_file = open(defconf.file_logfile,'r')
			wdict = {}
			for stringo in log_file:
				if dev[2] in stringo:
					string_splitted = stringo.split('\t')
					#times seen
					if times_seen == 0: #is it the oldest record?							
						first_seen = string_splitted[0]+' '+string_splitted[1]
					times_seen +=1
					# names
					hunt_name = string_splitted[4].strip()
					if hunt_name != 'n/a':
						if hunt_name != dev[3]:
							if hunt_name not in names_before:
								names_before.append(string_splitted[4])
								names_before_str=names_before_str+string_splitted[4]+', '		
					# places
					try:
						wdict[string_splitted[2]]+=1
					except KeyError:
						wdict[string_splitted[2]]=1
			log_file.close()
			
			places_str = ' '
			l = []
			for k,m in wdict.items(): l.append((m,k))
			l.sort()
			l.reverse()
			for m,k in l: places_str = places_str + k+'('+str(m)+')'+', '
			
			if names_before_str !='': names_before_str = ' | names seen: '+names_before_str[:-2]
			
			if places_str == ' ':
				places_str = 'nowhere before, '
			
			dev_info = "bt_addr: %s\nname: %s %s\ntimes seen: %s; first: %s; last: %s %s\nplaces: %s\ndevice type: %s\n\
device vendor: %s\nchip: %s | lmp version: %s\nservices: %s" \
				% (dev[2],dev[3],names_before_str,times_seen, first_seen,dev[0],dev[1],places_str[:-2],dev[4],dev[5],dev[6],dev[7],dev[8])
		else:
			dev_info = "bt_addr: %s\nname: %s\nlast seen: %s %s \ndevice type: %s\n\
device vendor: %s\nchip: %s | lmp version: %s\nservices: %s" \
				% (dev[2],dev[3],dev[0],dev[1],dev[4],dev[5],dev[6],dev[7],dev[8])
				
		self.monscreen.SetCellValue(a, 3,  dev_info)  #device info
		self.monscreen.SetCellTextColour(a, 3,  defconf.theme_bgcolor_displ)  #fxing somehow bug with invisibility of last column
	self.monscreen.ForceRefresh()

    def WriteToLog(self, devices):
        log_file = open(defconf.file_logfile,'a')
        for dev in devices:
		record = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
				% (dev[0],dev[1],defconf.user_location,dev[2],dev[3],dev[4],dev[5],dev[6],dev[7],dev[8].replace('\n',''))
		log_file.write(record)
	log_file.close()

    def OnSelectDevice(self, event):
	self.selected_device = self.monscreen.GetCellValue(event.GetRow(),1)
	self.tool_choiser.SetSelection(0)
	self.exploit_choiser.SetSelection(0)
	self.cmdline.SetValue(self.selected_device)
	self.selected_dev_info.SetLabel(self.monscreen.GetCellValue(event.GetRow(),3))

    def StopInquiryScan(self, event):
	self.inquiry_running = False
	self.PrintIntoLogger('aborting scan...\n')
	self.worker.abort()
	self.toolbar.EnableTool(ID_MF_TOOLBAR_SCAN_START, True)
	self.toolbar.EnableTool(ID_MF_TOOLBAR_SCAN_STOP, False)


    # TOOLS-EXPLOITING FUNCTIONS

    def OnExploitChose(self, event):
	if self.exploit_choiser.GetCurrentSelection() == 0: 
		pass
	else:
		self.tool_choiser.SetSelection(0)
		cmdline, description = self.expl[self.expl_list[self.exploit_choiser.GetCurrentSelection()]].split(';')
		cmdline.strip()
		self.logger.AppendText('> '+description.strip().replace('\\n','\n')+'\n')
		if self.selected_device: cmdline = cmdline.replace('@bt_addr@',self.selected_device)
		cmdline = cmdline.replace('@hci@', self.HCI_PLUG_DEVICE).replace('@hci_num@',self.HCI_PLUG_DEVICE[3:])
		self.cmdline.SetValue(cmdline)

    def OnToolChose(self, event):
	if self.tool_choiser.GetCurrentSelection() == 0: 
		pass
	else:
		self.exploit_choiser.SetSelection(0)
		cmdline, description = self.tools[self.tools_list[self.tool_choiser.GetCurrentSelection()]].split(';')
		cmdline.strip()
		self.logger.AppendText('> '+description.strip().replace('\\n','\n')+'\n')
		if self.selected_device: cmdline = cmdline.replace('@bt_addr@',self.selected_device)
		cmdline = cmdline.replace('@hci@', self.HCI_PLUG_DEVICE).replace('@hci_num@',self.HCI_PLUG_DEVICE[3:])
		self.cmdline.SetValue(cmdline)

    def RunTool(self, event):
	cmd = defconf.cmd_term +' '+self.cmdline.GetValue()
	subprocess.Popen(cmd.split())



class Frame_LocalDev(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, "local HCI devices settings", pos=(60, 60), size=(310, 182))

	# SOME VARIABLES
	self.current_hci = 'none'
	self.hci_list = ['none']
	self.curr_cod_mj = 'none'
	self.curr_cod_mi = 'none'

	# INTERFACE
	self.SetMinSize((310,182))
	self.SetMaxSize((310,182))
	self.CentreOnParent()
	fontl = wx.Font(defconf.theme_fontsize,wx.TELETYPE,wx.NORMAL,wx.NORMAL,False,u'Arial')
	self.panel = wx.Panel(self, style=wx.NO_BORDER)
	self.panel.SetBackgroundColour(defconf.theme_bgcolor)
	self.panel.SetForegroundColour(defconf.theme_fgcolor)
	self.panel.SetFont(fontl)

	self.hci_choicer = wx.Choice(self.panel, ID_LD_CHOICE_HCI, (248,6), (54,20), choices=self.hci_list)
	self.hci_choicer.Bind(wx.EVT_CHOICE, self.OnSelectHci, id=ID_LD_CHOICE_HCI)
	
	self.Reinit()
	
	self.f_bdaddr = wx.StaticText(self.panel,-1,"Bd Address: none", (48,30), (200,10))
	self.button_bdaddr = wx.Button(self.panel,ID_LD_BUTTON_BDADDR,"set", (6,25), (34,20))
	self.button_bdaddr.Bind(wx.EVT_BUTTON, self.ChangeBdaddr,id=ID_LD_BUTTON_BDADDR)
	
	self.f_name = wx.StaticText(self.panel,-1,"Name: none", (48,51), (200,10))
	self.button_name = wx.Button(self.panel,ID_LD_BUTTON_NAME,"set", (6,47), (34,20))
	self.button_name.Bind(wx.EVT_BUTTON, self.ChangeName,id=ID_LD_BUTTON_NAME)
	
	self.f_class = wx.StaticText(self.panel,-1,"Class: none", (48,72), (200,10))
	self.button_class = wx.Button(self.panel,ID_LD_BUTTON_CLASS,"set", (6,69), (34,20))
	self.button_class.Bind(wx.EVT_BUTTON, self.ChangeClass,id=ID_LD_BUTTON_CLASS)
	
	self.f_manufa = wx.StaticText(self.panel,-1,"Manufacturer: none", (50,92), (200,10))
	
	# checkboxes
	self.checkbox_visib = wx.CheckBox(self.panel,ID_LD_CHECKBOX_VISIBLE,"visibility", (10,109), (100,17))
	self.checkbox_visib.Bind(wx.EVT_CHECKBOX, self.OnCheckVisib,id=ID_LD_CHECKBOX_VISIBLE)

	self.checkbox_auth = wx.CheckBox(self.panel,ID_LD_CHECKBOX_AUTH,"autentification", (10,130), (100,17))
	self.checkbox_auth.Bind(wx.EVT_CHECKBOX, self.OnCheckAuth,id=ID_LD_CHECKBOX_AUTH)
	self.checkbox_encrypt = wx.CheckBox(self.panel,ID_LD_CHECKBOX_ENCRYPT,"encryption", (110,130), (100,17))
	self.checkbox_encrypt.Bind(wx.EVT_CHECKBOX, self.OnCheckEncrypt,id=ID_LD_CHECKBOX_ENCRYPT)
	self.checkbox_secmgr = wx.CheckBox(self.panel,ID_LD_CHECKBOX_SECMGR,"secmanager", (190,130), (100,17))
	self.checkbox_secmgr.Bind(wx.EVT_CHECKBOX, self.OnCheckSecmgr,id=ID_LD_CHECKBOX_SECMGR)

	# buttons bottom
	self.showmaxinfo_button = wx.Button(self.panel,ID_LD_BUTTON_SHOWMAXINFO,"show max info", (90,154), (90,20))
	self.showmaxinfo_button.Bind(wx.EVT_BUTTON, self.OnShowMaxInfo,id=ID_LD_BUTTON_SHOWMAXINFO)
	self.refresh_button = wx.Button(self.panel,ID_LD_BUTTON_REFRESH,"refresh", (183,154), (60,20))
	self.refresh_button.Bind(wx.EVT_BUTTON, self.OnRefresh,id=ID_LD_BUTTON_REFRESH)
	self.close_button = wx.Button(self.panel,ID_LD_BUTTON_CLOSE,"close", (246,154), (44,20))
	self.close_button.Bind(wx.EVT_BUTTON, self.OnClose,id=ID_LD_BUTTON_CLOSE)
	
	if self.hci_list[0]!='none':
		self.hci_choicer.SetSelection(0)
		self.OnSelectHci(None)

    # FUNCTIONS

    def Reinit(self): #UPDATES HCI LIST
	pos = self.hci_choicer.GetCurrentSelection()
	self.hci_list = []
	cmd_hciconfig_out = subprocess.Popen(defconf.cmd_hciconfig,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
	if cmd_hciconfig_out[0]:
		elements = cmd_hciconfig_out[0].split('\n\n')[:-1]
		for element in elements:
			self.hci_list.append(element[:4])
	else:
		self.hci_list = ['none']
		
	self.hci_choicer.Clear()
	self.hci_choicer.AppendItems(self.hci_list)
	self.hci_choicer.SetSelection(pos)

    def OnSelectHci(self, event):
	self.current_hci = self.hci_list[self.hci_choicer.GetCurrentSelection()]
	if self.current_hci != 'none':
		cmd_hciconfig_a = "%s -a %s" % (defconf.cmd_hciconfig, self.current_hci)
		cmd_hciconfig_out = subprocess.Popen(cmd_hciconfig_a.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
		if cmd_hciconfig_out[0]:
			elements = cmd_hciconfig_out[0].split('\n\t')
			self.checkbox_auth.SetValue(False)
			self.checkbox_encrypt.SetValue(False)
			self.checkbox_secmgr.SetValue(False)
			self.checkbox_visib.SetValue(False)
			for element in elements:
				if "BD Address" in element: self.f_bdaddr.SetLabel(element[:29])
				elif "Name" in element: self.f_name.SetLabel(element)
				elif "Class: 0" in element: self.f_class.SetLabel(element)
				elif "Manufacturer" in element: self.f_manufa.SetLabel(element)
				elif ("Device Class: " in element): self.curr_cod_mj = element[14:]
				elif ("Service Classes: " in element): self.curr_cod_mi = element[17:]
				if "AUTH" in element: self.checkbox_auth.SetValue(True)
				if "ENCRYPT" in element: self.checkbox_encrypt.SetValue(True)
				if "SECMGR" in element: self.checkbox_secmgr.SetValue(True)
				if "PSCAN" in element: self.checkbox_visib.SetValue(True)
				if "ISCAN" in element: self.checkbox_visib.SetValue(True)
		else:
			self.hci_list = ['none']
	else:
		self.checkbox_auth.SetValue(False)
		self.checkbox_encrypt.SetValue(False)
		self.checkbox_secmgr.SetValue(False)
		self.checkbox_visib.SetValue(False)
		self.f_bdaddr.SetLabel('Bd Address: none')
		self.f_name.SetLabel('Name: none')
		self.f_class.SetLabel('Class: none')
		self.f_manufa.SetLabel('Manufacturer: none')
		self.curr_cod_mj = 'none'
		self.curr_cod_mi = 'none'
	self.Reinit()
	frame_main.HciListRefresh()	
	
    def ChangeBdaddr(self, event):
	curr_bdaddr = self.f_bdaddr.GetLabel()[12:]
	dialog = wx.TextEntryDialog(self, "set bd_addr using 'bdaddr' tool", "change bdaddr", curr_bdaddr, style=wx.OK|wx.CANCEL)
	if dialog.ShowModal() == wx.ID_OK:
		cmd = "%s -i %s %s" % (defconf.cmd_bdaddr, self.current_hci, dialog.GetValue().strip())
		cmd_out = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
		if 'Address changed' in cmd_out[0]:
			if 'Warning!' in cmd_out[0]:
				raiser = wx.MessageDialog(None, "no verified support of bdaddr\nfor specified device!\nBD_ADDR may not be changed!", "bdaddr", wx.OK | wx.ICON_EXCLAMATION)
				if raiser.ShowModal() == wx.ID_YES: raiser.Destroy()
			cmd = "%s -a %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_reset)
			cmd_out = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
			if cmd_out !=('',''):
				raiser = wx.MessageDialog(None, "can't reset device!\nReset it manually!", "bdaddr", wx.OK | wx.ICON_ERROR)
				if raiser.ShowModal() == wx.ID_YES: raiser.Destroy()
		self.OnSelectHci(None)
		if curr_bdaddr != self.f_bdaddr.GetLabel()[12:]:
			raiser = wx.MessageDialog(None, "w00a! BD_ADDR of device changed!", "bdaddr", wx.OK | wx.ICON_INFORMATION)
		else:
			raiser = wx.MessageDialog(None, "err.. bdaddr can't change\nBD_ADDR of specified device.\ntrying to do it with bccmd!", "bdaddr", wx.OK | wx.ICON_ERROR)
			if raiser.ShowModal() == wx.ID_YES: raiser.Destroy()
			baddr = dialog.GetValue().strip().upper().split(":")
			cmd = "%s -d %s psset -r bdaddr 0x%s 0x%s 0x%s 0x%s 0x%s 0x%s 0x%s 0x%s" % (
				defconf.cmd_bccmd, self.current_hci, baddr[3], "00", baddr[5], baddr[4], baddr[2], "00", baddr[1], baddr[0])
			subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
			progress_max = 20
			progress_win = wx.ProgressDialog("progress","bccmd working...", progress_max, style=wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)
			keepGoing = True
			count = 0
			while keepGoing and count < progress_max:
				count+=1
				sleep(1)
				keepGoing = progress_win.Update(count)
			progress_win.Destroy()
			self.OnSelectHci(None)
			if curr_bdaddr != self.f_bdaddr.GetLabel()[12:]:
				raiser = wx.MessageDialog(None, "w00a! BD_ADDR of device changed!", "bccmd", wx.OK | wx.ICON_INFORMATION)
			else:
				raiser = wx.MessageDialog(None, "err.. bccmd can't change\nBD_ADDR of specified device.", "bccmd", wx.OK | wx.ICON_ERROR)
		if raiser.ShowModal() == wx.ID_YES: raiser.Destroy()

    def ChangeName(self, event):
	dialog = wx.TextEntryDialog(self, "set new name for device", "change name", self.f_name.GetLabel()[7:-1], style=wx.OK|wx.CANCEL)
	if dialog.ShowModal() == wx.ID_OK:
		cmd = "%s -a %s %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_name, dialog.GetValue())
		cmd_out = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
		if cmd_out !=('',''):
			raiser = wx.MessageDialog(None, "some error?", "change name of device", wx.OK | wx.ICON_ERROR)
			if raiser.ShowModal() == wx.ID_YES: raiser.Destroy()
		self.OnSelectHci(None)

    def ChangeClass(self, event):
	dialog_message = "current Device Class:\n   %s \n\ncurrent Service Classes:\n   %s \n\nset new Class of Device (hex value):"\
		% (self.curr_cod_mj, self.curr_cod_mi)
	dialog = wx.TextEntryDialog(self, dialog_message, "change CoD", self.f_class.GetLabel()[7:], style=wx.OK|wx.CANCEL)
	if dialog.ShowModal() == wx.ID_OK:
		cmd = "%s -a %s %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_class, dialog.GetValue())
		cmd_out = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
		if cmd_out !=('',''):
			raiser = wx.MessageDialog(None, "some error?", "change name of device", wx.OK | wx.ICON_ERROR)
			touch = raiser.ShowModal()
			if touch == wx.ID_YES: raiser.Destroy()
		self.OnSelectHci(None)

    def OnCheckAuth(self, event):
	if self.checkbox_auth.GetValue():
		cmd = "%s -a %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_auth)
		subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
	else:
		cmd = "%s -a %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_noauth)
		subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

    def OnCheckEncrypt(self, event):
	if self.checkbox_encrypt.GetValue():
		cmd = "%s -a %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_encrypt)
		subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
		self.checkbox_auth.SetValue(True)
	else:
		cmd = "%s -a %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_noencrypt)
		subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

    def OnCheckSecmgr(self, event):
	if self.checkbox_secmgr.GetValue():
		cmd = "%s -a %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_secmgr)
		subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
	else:
		cmd = "%s -a %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_nosecmgr)
		subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

    def OnCheckVisib(self, event):
	if self.checkbox_visib.GetValue():
		cmd = "%s -a %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_piscan)
		subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
	else:
		cmd = "%s -a %s %s" % (defconf.cmd_hciconfig, self.current_hci, defconf.cmd_hciconfig_cmd_noscan)
		subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

    def OnShowMaxInfo(self, event):
	filename = '/dev/null'
	raiser = wx.MessageDialog(None, "save results to file?", "show max info about local HCI device", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
	if raiser.ShowModal() == wx.ID_YES:
		dialog = wx.FileDialog(self, "save as", os.getcwd(), style=wx.SAVE|wx.OVERWRITE_PROMPT)
		if dialog.ShowModal() == wx.ID_OK:
			filename = dialog.GetPath()			
	raiser.Destroy()
	cmd = "%s %s %s %s" % (defconf.cmd_term, defconf.cmd_getmaxlocaldevinfo, self.current_hci, filename)
	subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

    def OnRefresh(self, event):
	self.Reinit()
	self.OnSelectHci(None)

    def OnClose(self, event):
	self.Destroy()



class AboutBout(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, "about", pos=(60, 60), size=(300, 390))

	# INTERFACE
	self.SetMinSize((300,390))
	self.SetMaxSize((300,390))
	self.CentreOnParent()
	fontl = wx.Font(defconf.theme_fontsize,wx.TELETYPE,wx.NORMAL,wx.NORMAL,False,u'Arial')
	self.panel = wx.Panel(self, style=wx.NO_BORDER)
	self.panel.SetBackgroundColour(defconf.theme_bgcolor)
	self.panel.SetForegroundColour(defconf.theme_fgcolor)
	self.panel.SetFont(fontl)

	message_himeko = "Himeko is a wastefully energetic girl from anime named Pani Poni Dash, who often shouts \"maho\", possibly her ways of saying \"what\", \"cool\", etc, while speaking. She frequently annoys the other students in her class with her antics and inability to carry a straight train of thought. Her \"ahoge\" (the lock of hair on her head, or as we call it in America, \"cowlick\") contains a mysterious power that gives Himeko her limitless energy and is capable of movement on its own accord."
	message_ver =("""%s %s
			   \nhttp:\\\\wiki.thc.org\\bluemaho
			   \n^_^""") % (NAME, VERSION)
			   
	img = wx.Image("config/themes/maho/himeko.jpg", wx.BITMAP_TYPE_ANY)
	wx.StaticBitmap(self.panel, -1, wx.BitmapFromImage(img),(0,0),(300,169))

	wx.StaticText(self.panel,-1,message_himeko, (4,174), (290,180))
	wx.StaticText(self.panel,-1,message_ver, (4,320), (290,180), wx.ALIGN_CENTER)

	self.close_button = wx.Button(self.panel,ID_LD_BUTTON_CLOSE,"close", (246,154), (44,20))
	self.close_button.Bind(wx.EVT_BUTTON, self.OnClose,id=ID_LD_BUTTON_CLOSE)
	
    def OnClose(self, event):
		self.Destroy()



class Handbook(wx.Frame):
	def __init__(self, parent, title):
		wx.Frame.__init__(self, parent, -1, "handbook", pos=(60, 60), size=(355, 400))

		# INTERFACE
		self.SetMinSize((355,400))
		self.SetMaxSize((355,400))
		self.CentreOnParent()
		fontl = wx.Font(defconf.theme_fontsize,wx.TELETYPE,wx.NORMAL,wx.NORMAL,False,u'Arial')
		self.panel = wx.Panel(self, style=wx.NO_BORDER)
		self.panel.SetBackgroundColour(defconf.theme_bgcolor)
		self.panel.SetForegroundColour(defconf.theme_fgcolor)
		self.panel.SetFont(fontl)

		file = open(defconf.file_handbook,'r')
		self.hb_dic = {' select page':''}
		self.content = ''
		title = ''
		for line in file:
			if '### TITLE =' in line:
				title = line.split('=')[1].strip()
			elif '### END ###' in line:
				self.hb_dic[title] = self.content
				self.content = ''
			else:
				self.content = self.content +' '+line
		file.close()
		self.hb_list = self.hb_dic.keys()
		self.hb_list.sort()	
	
		self.hb_choiser = wx.Choice(self.panel,2212,wx.Point(3,6), wx.Size(348,20),choices=self.hb_list,style = wx.CB_DROPDOWN)
		self.hb_choiser.Bind(wx.EVT_CHOICE, self.OnPageChose, id=2212)

		self.viewer = wx.TextCtrl(self.panel, -1,'',wx.Point(2,30), wx.Size(349,350),wx.TE_MULTILINE | wx.TE_READONLY)
		self.viewer.SetFont(wx.Font(defconf.theme_fontsize_hb,wx.TELETYPE,wx.NORMAL,wx.NORMAL,False,u'Arial'))

	def OnPageChose(self, event):
		if self.hb_choiser.GetCurrentSelection() == 0: 
			pass
		else:
			self.content = self.hb_dic[self.hb_list[self.hb_choiser.GetCurrentSelection()]]
			self.viewer.SetValue(self.content)


class Stat(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, "statistics", pos=(60, 60), size=(370, 130))

	# INTERFACE
	self.SetMinSize((370,130))
	self.SetMaxSize((370,130))
	self.CentreOnParent()
	fontl = wx.Font(defconf.theme_fontsize,wx.TELETYPE,wx.NORMAL,wx.NORMAL,False,u'Arial')
	self.panel = wx.Panel(self, style=wx.NO_BORDER)
	self.panel.SetBackgroundColour(defconf.theme_bgcolor)
	self.panel.SetForegroundColour(defconf.theme_fgcolor)
	self.panel.SetFont(fontl)
			   
	wx.StaticText(self.panel,-1,"  input", (6,8), (50,12)) #h,v
	self.fopenline = wx.TextCtrl(self.panel, -1, "",wx.Point(48,4), wx.Size(260,20))
	self.fopen_button = wx.Button(self.panel,ID_LD_BUTTON_CLOSE,"choose", (312,4), (50,20))
	self.fopen_button.Bind(wx.EVT_BUTTON, self.OnFopen,id=ID_LD_BUTTON_CLOSE)

	wx.StaticText(self.panel,-1,"output", (6,36), (50,12))
	self.fsaveline = wx.TextCtrl(self.panel, -1, "",wx.Point(48,32), wx.Size(260,20))
	self.fsave_button = wx.Button(self.panel,ID_LD_BUTTON_CLOSE,"choose", (312,32), (50,20))
	self.fsave_button.Bind(wx.EVT_BUTTON, self.OnFsave,id=ID_LD_BUTTON_CLOSE)

	wx.StaticText(self.panel,-1,"   from", (6,64), (50,12))
	self.fromdate = wx.TextCtrl(self.panel, -1, "",wx.Point(48,60), wx.Size(76,20))
	wx.StaticText(self.panel,-1,"to", (132,64), (50,12))
	self.todate = wx.TextCtrl(self.panel, -1, "",wx.Point(148,60), wx.Size(76,20))

	self.checkbox_hs = wx.CheckBox(self.panel,ID_ST_HOURS_STAT,"stat by hours",(240,64),(100,17))

	self.run_button = wx.Button(self.panel,ID_ST_BUTTON_RUN,"run", (240,100), (44,20))
	self.run_button.Bind(wx.EVT_BUTTON, self.OnRun,id=ID_ST_BUTTON_RUN)

	self.close_button = wx.Button(self.panel,ID_ST_BUTTON_CLOSE,"cancel", (300,100), (44,20))
	self.close_button.Bind(wx.EVT_BUTTON, self.OnClose,id=ID_ST_BUTTON_CLOSE)
		
    def OnRun(self, event):
	def day_of_week(a): # a = yyyy.mm.dd
		dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
		return "%s" % (dayofWeek[date.weekday(date(int(a.split('-')[0]), int(a.split('-')[1]), int(a.split('-')[2])))])

	if self.fopenline.GetValue()=='' or self.fsaveline.GetValue()=='':
		raiser = wx.MessageDialog(None, "Not all required fields were filled?", "run",wx.OK | wx.ICON_ERROR)
		if raiser.ShowModal() == wx.ID_YES: raiser.Destroy()
	else:
		file_input_name = self.fopenline.GetValue()
		file_input = open(file_input_name,"r")
		file_output = open(self.fsaveline.GetValue(),"w")
		date_start = self.fromdate.GetValue() #yyyy-mm-dd
		date_end = self.todate.GetValue()
		hours_flag = self.checkbox_hs.GetValue()

		file_output.write(" <meta http-equiv=\"Content-Type\" content=\"text/html;\">\
			<style type=\"text/css\">\n \
			body{color: #000000; font-family: Verdana, Arial, Sans-Serif; font-size: 11px;}\n \
			td{color:#000000; font-family: Verdana, Arial, Sans-Serif; font-size: 10px; margin: 3px;}\n \
			</style>\n\
			<title>bluemaho statistics</title>\n\
			<center>\n")

		buf_time = []
		buf_name = []
		buf_date = []
		buf_udevs = []
		buf_sdp = []
		buf_udevs_sdp = []
		buf_chiplmp = []
		buf_addr = []
		
		for n in file_input:
		  ns = n.split('\t')
		  # 0 date 1 time 2 place 3 addr 4 name 5 cod 6 vendor 7 chip 8 lmp 9 sdp
		  if ns[0]>=date_start and ns[0]<=date_end:
			if (ns[4].strip() not in buf_name) and ('n/a' not in ns[4]): # uniq names
				buf_name.append(ns[4].strip())
			if (ns[3]) not in buf_addr: # uniq addr
				buf_addr.append((ns[3]))
			if (ns[0],ns[1][:-3],ns[3]) not in buf_time: #uniq dev per one hour
				buf_time.append((ns[0],ns[1][:-3],ns[3]))
			if (ns[0],ns[3]) not in buf_date: #uniq dev per day
				buf_date.append((ns[0],ns[3]))
			if (ns[3],ns[5],ns[6]) not in buf_udevs: # class + ven
				buf_udevs.append((ns[3],ns[5],ns[6]))
			if ((ns[3],ns[7][:-5],ns[8]) not in buf_chiplmp) and (ns[7]!='') and (ns[8]!='error') and (ns[8]!='unknown'): # chip, lmp
				buf_chiplmp.append((ns[3],ns[7][:-5],ns[8]))
			if (ns[3] not in buf_sdp) and ('unknown' not in ns[9]) and ('error' not in ns[9]) and ('services found' not in ns[9] and ('undiscovered' not in ns[9])) and (ns[9]!=''):
				buf_sdp.append(ns[3])
				sdp_services = ns[9].split(',')
				for n in sdp_services:
					buf_udevs_sdp.append(n.strip())
		
		dev_count = len(buf_addr)

		file_output.write("<br><br><table width=500>\n")
		file_output.write("<tr><td bgcolor=dddddd><center><h3>bluemaho statistics from %s to %s<br></h3> input file: %s, unique devices: %s<br><br></h3></td></tr></table><br><br>\n" % (date_start, date_end, file_input_name, dev_count))

		# uniq names
		file_output.write("<table width=510><tr bgcolor=eeeeee><td><center><h3>unique names</h3></b></td></tr></table>\n")
		file_output.write("<table width=500 cellpadding=0 cellspacing=0>\n")
		file_output.write("<tr><td>\n")
		buf_name.sort()
		for a in buf_name:
			file_output.write(a+' | ')
		file_output.write("</td></tr></table><br><br>\n")
		buf_name = []

		# days and hours (dirty code)
		if hours_flag:
			file_output.write("<table width=510><tr bgcolor=eeeeee><td><center><h3>uniq devices per day</h3></b></td></tr></table>\n")
			file_output.write("<table width=500 cellpadding=0 cellspacing=0>\n")
			file_output.write("<tr><td valign=top>\n")
			d_buf = []
			n_buf = {}
			old_date =  buf_time[0][0]
			file_output.write('<b>'+old_date+' '+day_of_week(old_date)+'</b><br>')
			d_buf.append(old_date)
			for (a,b,c) in buf_time:
				if a not in d_buf:
					d_buf.append(a)
					l = []
					for k,m in n_buf.items(): l.append((m,k))
					l.sort()
					l.reverse()
					zoom = l[0][0]
					if zoom > 50: zoom = (zoom/50)+1
					else: zoom = 1
					l = []
					for k,m in n_buf.items(): l.append((k,m))
					l.sort()
					for m,k in l:
						file_output.write("&nbsp;&nbsp;&nbsp;%s =%s %s<br>" % (m,'='*(k/zoom),k))
					file_output.write('<br><b>'+a+' '+day_of_week(a)+'</b><br>')
					n_buf = {}
				if a in d_buf:
					try: n_buf[b]+=1
					except KeyError: n_buf[b]=1
			l = []
			zoom = 1
			for k,m in n_buf.items():
				if zoom < m: zoom = m
				l.append((k,m))
			l.sort()
			if zoom > 45: zoom = (zoom/45)+1
			else: zoom = 1
			for m,k in l:
				file_output.write("&nbsp;&nbsp;%s =%s %s<br>" % (m,'='*(k/zoom),k))
			file_output.write("<br></td></tr></table>\n")

		# days/devices
		buf = {}
		for (a,b) in buf_date:
			try: buf[a]+=1
			except KeyError: buf[a]=1
		file_output.write("<table width=510><tr bgcolor=eeeeee><td><center><h3>uniq devices per day</h3></b></td></tr></table>\n")
		file_output.write("<table width=500 cellpadding=0 cellspacing=0>\n")
		l = []
		zoom = 1
		for k,m in buf.items():
			if zoom < m: zoom = m
			l.append((k,m))
		l.sort()
		if zoom > 45: zoom = (zoom/45)+1
		else: zoom = 1
		for m,k in l:
			file_output.write("<tr><td>%s %s =%s %s</td></tr>\n" %(m,day_of_week(m),'='*(k/zoom),k))
		file_output.write("</table><br><br>\n")

		# time/devices
		buf = {}
		for (a,b,c) in buf_time:
			try: buf[b]+=1
			except KeyError: buf[b]=1
		file_output.write("<table width=510><tr bgcolor=eeeeee><td><center><h3>uniq devices per hour</h3></b></td></tr></table>\n")
		file_output.write("<table width=500 cellpadding=0 cellspacing=0>\n")
		l = []
		zoom = 1
		for k,m in buf.items():
			if zoom < m: zoom = m
			l.append((k,m))
		l.sort()
		if zoom > 45: zoom = (zoom/45)+1
		else: zoom = 1
		for m,k in l:
			file_output.write("<tr><td>%s =%s %s</td></tr>\n" %(m,'='*(k/zoom),k))
		file_output.write("</table><br><br>\n")

		# vendor
		buf = {}
		for (a,b,c) in buf_udevs:
			try: buf[c]+=1
			except KeyError: buf[c]=1
		file_output.write("<table width=510><tr bgcolor=eeeeee><td><center><h3>device vendors</h3></b></td></tr></table>\n")
		file_output.write("<table width=500 cellpadding=0 cellspacing=0>\n")
		file_output.write("<tr><td></td><td width=50></td><td></td></tr>\n")
		c = len(buf_udevs)
		l = []
		for k,m in buf.items(): l.append((m,k))
		l.sort()
		l.reverse()
		for k,m in l:
			file_output.write("<tr><td>%s</td><td>%.2f%%</td><td>%s</td></tr>\n" %(m,((1.0*k/c)*100),k))
		file_output.write("</table><br><br>\n")

		# chip
		buf = {}
		for (a,b,c) in buf_chiplmp:
			if b == 'un': b = 'unknown'
			try: buf[b]+=1
			except KeyError: buf[b]=1
		file_output.write("<table width=510><tr bgcolor=eeeeee><td><center><h3>chip manufacturers</h3></b></td></tr></table>\n")
		file_output.write("<table width=500 cellpadding=0 cellspacing=0>\n")
		file_output.write("<tr><td></td><td width=50></td><td></td></tr>\n")
		c = len(buf_chiplmp)
		l = []
		for k,m in buf.items(): l.append((m,k))
		l.sort()
		l.reverse()
		for k,m in l:
			file_output.write("<tr><td>%s</td><td>%.2f%%</td><td>%s</td></tr>\n" %(m,((1.0*k/c)*100),k))
		file_output.write("</table><br><br>\n")

		# class of devices
		buf = {}
		for (a,b,c) in buf_udevs:
			try: buf[b]+=1
			except KeyError: buf[b]=1
		file_output.write("<table width=510><tr bgcolor=eeeeee><td><center><h3>class of devices</h3></b></td></tr></table>\n")
		file_output.write("<table width=500 cellpadding=0 cellspacing=0>\n")
		file_output.write("<tr><td></td><td width=50></td><td></td></tr>\n")
		c = len(buf_udevs)
		l = []
		for k,m in buf.items(): l.append((m,k))
		l.sort()
		l.reverse()
		for k,m in l:
			file_output.write("<tr><td>%s</td><td>%.2f%%</td><td>%s</td></tr>\n" %(m,((1.0*k/c)*100),k))
		file_output.write("</table><br><br>\n")

		# lmp
		buf = {}
		for (a,b,c) in buf_chiplmp:
			try: buf[c]+=1
			except KeyError: buf[c]=1
		file_output.write("<table width=510><tr bgcolor=eeeeee><td><center><h3>LMP version</h3></b></td></tr></table>\n")
		file_output.write("<table width=500 cellpadding=0 cellspacing=0>\n")
		file_output.write("<tr><td></td><td width=50></td><td width=40></td></tr>\n")
		c = len(buf_chiplmp)
		l = []
		for k,m in buf.items(): l.append((m,k))
		l.sort()
		l.reverse()
		for k,m in l:
			file_output.write("<tr><td>%s</td><td>%.2f%%</td><td>%s</td></tr>\n" %(m,((1.0*k/c)*100),k))
		file_output.write("</table><br><br>\n")

		# sdp
		buf = {}
		for a in buf_udevs_sdp:
			if a!='':
				try: buf[a]+=1
				except KeyError: buf[a]=1
		file_output.write("<table width=510><tr bgcolor=eeeeee><td><center><h3>services</h3></b></td></tr></table>\n")
		file_output.write("<table width=500 cellpadding=0 cellspacing=0>\n")
		file_output.write("<tr><td></td><td width=50></td><td></td></tr>\n")
		c = len(buf_udevs_sdp)
		l = []
		for k,m in buf.items(): l.append((m,k))
		l.sort()
		l.reverse()
		for k,m in l:
			file_output.write("<tr><td>%s</td><td>%.2f%%</td><td>%s</td></tr>\n" %(m,((1.0*k/c)*100),k))
		file_output.write("</table><br><br>\n")

		file_output.write("<br><br><br>^_^\n")

		file_input.close()
		file_output.close()

		raiser = wx.MessageDialog(None, "Statistics formed, sir!", "run",wx.OK | wx.ICON_INFORMATION)
		if raiser.ShowModal() == wx.ID_YES:
			raiser.Destroy()
			#?self.Destroy()
	
    def OnClose(self, event):
	self.Destroy()
		
    def OnFopen(self, event):
	fopendialog = wx.FileDialog(self.panel, style=wx.OPEN)
	if fopendialog.ShowModal() == wx.ID_OK:
		try:
			f = open(fopendialog.GetPath(),"r")
			date_start = f.readline().split('\t')[0]
			date_end = date_start
			for n in f:
				if n.split('\t')[0]>date_end: date_end = n.split('\t')[0]
			self.fopenline.SetValue(fopendialog.GetPath())
			f.close()
			self.fromdate.SetValue(date_start)
			self.todate.SetValue(date_end)
		except:
			raiser = wx.MessageDialog(None, "can't correctly parse specifyed input file! sorry, man..", "fopen",wx.OK | wx.ICON_ERROR)
			if raiser.ShowModal() == wx.ID_YES: raiser.Destroy()
	
    def OnFsave(self, event):
	fsavedialog = wx.FileDialog(self.panel, style=wx.SAVE)
	if fsavedialog.ShowModal() == wx.ID_OK:
		self.fsaveline.SetValue((fsavedialog.GetPath())+'.html')



# CLASS FOR GLOBAL VARIABLES FROM CONFIG
class defconf:
	pass

# READ DEFAULT CONFIGURATION
def ReadDefaultConfiguration(filename):
	def parse(line):
		pair = line.split('=')
		pair[0] = pair[0].strip()
		pair[1] = pair[1].strip()
		return pair

	file = open(filename,'r')
	for line in file:
		if line[0] !='#':
			pair = parse(line)
			if    pair[0] == 'theme': defconf.theme = pair[1]
			elif pair[0] == 'theme_file_colors':
				file_c = open(defconf.theme+pair[1],'r')
				for line_c in file_c:
					if line_c[0] !='#':
						pair_c = parse(line_c)
						if pair_c[0] == 'bgcolor': defconf.theme_bgcolor = pair_c[1]
						elif pair_c[0] == 'fgcolor': defconf.theme_fgcolor = pair_c[1]
						elif pair_c[0] == 'bgcolor_displ': defconf.theme_bgcolor_displ = pair_c[1]
						elif pair_c[0] == 'fontsize': defconf.theme_fontsize = int(pair_c[1])
						elif pair_c[0] == 'fontsize_dev': defconf.theme_fontsize_dev = int(pair_c[1])
						elif pair_c[0] == 'fontsize_log': defconf.theme_fontsize_log = int(pair_c[1])
						elif pair_c[0] == 'fontsize_hb': defconf.theme_fontsize_hb = int(pair_c[1])
				file_c.close()
			elif pair[0] == 'theme_ico_main': defconf.theme_ico_main = defconf.theme+pair[1]
			elif pair[0] == 'theme_ico_tb_exit': defconf.theme_ico_tb_exit = defconf.theme+pair[1]
			elif pair[0] == 'theme_ico_tb_about': defconf.theme_ico_tb_about = defconf.theme+pair[1]
			elif pair[0] == 'theme_ico_tb_dev': defconf.theme_ico_tb_dev = defconf.theme+pair[1]
			elif pair[0] == 'theme_ico_tb_run': defconf.theme_ico_tb_run = defconf.theme+pair[1]
			elif pair[0] == 'theme_ico_tb_stop': defconf.theme_ico_tb_stop = defconf.theme+pair[1]
			elif pair[0] == 'theme_ico_tb_location': defconf.theme_ico_tb_location = defconf.theme+pair[1]
			elif pair[0] == 'theme_ico_tb_handbook': defconf.theme_ico_tb_handbook = defconf.theme+pair[1]
			elif pair[0] == 'theme_ico_tb_stat': defconf.theme_ico_tb_stat = defconf.theme+pair[1]
			elif pair[0] == 'theme_img_dborder': defconf.theme_img_dborder = defconf.theme+pair[1]
			elif pair[0] == 'theme_snd_onnewdev': defconf.theme_snd_onnewdev = defconf.theme+pair[1]
			elif pair[0] == 'file_oui': defconf.file_oui = pair[1]
			elif pair[0] == 'file_tools_list': defconf.file_tools_list = pair[1]
			elif pair[0] == 'file_exploits_list': defconf.file_exploits_list = pair[1]
			elif pair[0] == 'file_logfile': defconf.file_logfile = pair[1]
			elif pair[0] == 'file_on_new_dev_found': defconf.file_on_new_dev_found = pair[1]
			elif pair[0] == 'file_handbook': defconf.file_handbook = pair[1]
			elif pair[0] == 'cmd_bccmd': defconf.cmd_bccmd = pair[1]
			elif pair[0] == 'cmd_bdaddr': defconf.cmd_bdaddr = pair[1]
			elif pair[0] == 'cmd_getmaxlocaldevinfo': defconf.cmd_getmaxlocaldevinfo = pair[1]
			elif pair[0] == 'cmd_hciconfig': defconf.cmd_hciconfig = pair[1]
			elif pair[0] == 'cmd_hcitool_scan': defconf.cmd_hcitool_scan = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_auth': defconf.cmd_hciconfig_cmd_auth = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_noauth': defconf.cmd_hciconfig_cmd_noauth = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_encrypt': defconf.cmd_hciconfig_cmd_encrypt = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_noencrypt': defconf.cmd_hciconfig_cmd_noencrypt = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_secmgr': defconf.cmd_hciconfig_cmd_secmgr = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_nosecmgr': defconf.cmd_hciconfig_cmd_nosecmgr = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_piscan': defconf.cmd_hciconfig_cmd_piscan = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_noscan': defconf.cmd_hciconfig_cmd_noscan = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_name': defconf.cmd_hciconfig_cmd_name = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_class': defconf.cmd_hciconfig_cmd_class = pair[1]
			elif pair[0] == 'cmd_hciconfig_cmd_reset': defconf.cmd_hciconfig_cmd_reset = pair[1]
			elif pair[0] == 'cmd_sdp_browse': defconf.cmd_sdp_browse = pair[1]
			elif pair[0] == 'cmd_term': defconf.cmd_term = pair[1]
			elif pair[0] == 'horizontal_pos': defconf.horizontal_pos = int(pair[1])
			elif pair[0] == 'vertical_pos': defconf.vertical_pos = int(pair[1])
			elif pair[0] == 'user_location': defconf.user_location = pair[1]
			elif pair[0] == 'flag_do_sdp': defconf.flag_do_sdp = bool(pair[1])
			elif pair[0] == 'flag_log': defconf.flag_log = bool(pair[1])
			elif pair[0] == 'flag_loop_scan': defconf.flag_loop_scan = bool(pair[1])
			elif pair[0] == 'flag_onnewdev': defconf.flag_onnewdev = bool(pair[1])
			elif pair[0] == 'flag_sound': defconf.flag_sound = bool(pair[1])
			elif pair[0] == 'flag_trackinfo': defconf.flag_trackinfo = bool(pair[1])
	file.close()


# SET VERBOSE IF NEEDED
if '-v' in sys.argv:
	verbose = True
else:
	verbose = False

# READ CONFIGURATION FROM 'CONFIG_FILENAME'
if verbose: print "[0] Reading configuration from " + CONFIG_FILENAME
ReadDefaultConfiguration(CONFIG_FILENAME)
if verbose: print "[1] Using theme: " +defconf.theme

# MAKE VISUAL
if verbose:
	app = wx.App(redirect=False, clearSigInt=True)
else:
	app = wx.App(redirect=True, filename=None)

frame_main = Frame_Main()
app.SetTopWindow(frame_main)
frame_main.Show(True)
app.MainLoop()