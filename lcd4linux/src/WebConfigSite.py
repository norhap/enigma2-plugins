from glob import glob
from os import stat
from os.path import isfile, join, basename
from pathlib import Path
from time import time
from twisted.web import resource, http
from html import unescape as _unescape

from enigma import eTimer
from Components.config import ConfigSelection, ConfigYesNo, ConfigText, ConfigSlider, ConfigClock, ConfigPassword
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CONFIG
from .module import L4Lelement
from .plugin import L4log, L4logE, getScreenActive, setConfigMode, setisMediaPlayer, setConfigStandby, getConfigStandby, getisMediaPlayer, getBilder
from .plugin import L4LoadNewConfig, ConfTimeCheck, rmFile, rmFiles, setPopText, setScreenActive, getSaveEventListChanged, setSaveEventListChanged
from .plugin import getMJPEGreader, xmlRead, xmlWrite, xmlClear, xmlDelete, xmlSkin, MJPEG_stop, MJPEG_start, setFONT, resetWetter, resetCal
from .plugin import getWWW, getINFO, getTMPL, getConfigMode, PopText, Version, WWWpic, PICfritz, LCD4linux, LCD4config, CrashFile
from . import _

from .configOptions import L1, L2, L3, L4

M = [
	_("OSD"), _("Screen"), _("Picture"), _("Weather"), _("Netatmo"), _("Popup-Text"), _("FritzCall"), _("Font"), _("Mail"), _("Calendar"),
	_("Remote Box"), _("WWW Converter"), _("WebIF"), _("MJPEG Stream"), _("Box-Skin-LCD"), _("Tuner"), _("Key"), _("BlueSound"), _("Sonos"),
	_("MusicCast")
	]
Mode = "1"
ModeOld = ""
Element = ""
ElementList = []
ExeMode = False
StatusMode = False
L4LElement = L4Lelement()


def _exec(command):
	variable = command.split(" ", 1)[0]
	exec(f"global {variable};{command}")


def _l(st):
	if isinstance(st, bytes):
		st = st.decode("utf-8", "ignore")
	return st.replace(" [ok]>", "").encode('ascii', 'xmlcharrefreplace').decode()


def AktiveMode(Test, R):
	Aktiv, Color = ("checked", 'style=\"color: #FFCC00\"') if Mode == Test else ("", "")
	return Aktiv, Color, R


def AktiveElement(Test):
	Aktiv, Color = ("checked", 'style=\"color: #FFCC00\"') if Element == Test else ("", "")
	return Aktiv, Color


def AktiveScreen(Test):
	return "; background-color:lime" if getScreenActive() == Test else "; background-color:ButtonFace"

########################################################


class LCD4linuxConfigweb(resource.Resource):
	title = "L4L Webinterface"
	isLeaf = True
	RestartGUI = False

	def __init__(self):
		self.StatusTimer = eTimer()
		self.StatusTimer.callback.append(self.resetWeb)
		self.CurrentMode = ("-", "-")

	def resetWeb(self):
		L4log("Reset Web")
		self.StatusTimer.stop()
		setConfigMode(False)
		setisMediaPlayer(self.CurrentMode[1])
		setConfigStandby(self.CurrentMode[0])
		self.CurrentMode = ("-", "-")

	def restartTimer(self):
		L4log("Restart Timer")
		self.StatusTimer.stop()
		self.StatusTimer.startLongTimer(60)

	def sendTextFile(self, req, disposition, fileName):
		req.setHeader('Content-type', 'text/plain')
		req.setHeader('Content-Disposition', disposition)
		req.setHeader('Content-Length', str(stat(fileName).st_size))
		req.setHeader('charset', 'UTF-8')
		return Path(fileName).read_bytes()

	def render_GET(self, request):
		L4logE("GET received", request.args)
		return self.action(request)

	def render_POST(self, request):
		L4logE("POST received", request.args)
		return self.action(request)

	def action(self, req):
		global Mode, ModeOld, Element, ElementList, ExeMode, StatusMode
		IP = req.getClientIP()
		L4logE("IP1:", IP)
		if IP is None:
			L4logE("IP2:", req.client.host)
			IP = req.client.host.split(":")[-1] if "." in req.client.host else None
		else:
			IP = IP.split(":")[-1]
		if IP is None:
			Block = False
		else:
			Block = True
			WL = LCD4linux.WebIfAllow.value
			for x in WL.split():
				if IP.startswith(x):
					Block = False
					break
			if "*" in WL:
				Block = False
			WL = LCD4linux.WebIfDeny.value
			for x in WL.split():
				if IP.startswith(x):
					Block = True
					break
		if Block is True:
			html = "<html>"
			html += "<head>\n"
			html += "<meta http-equiv=\"Content-Language\" content=\"de\">\n"
			html += "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=windows-1252\">\n"
			html += "<meta http-equiv=\"cache-control\" content=\"no-cache\" />\n"
			html += "<meta http-equiv=\"pragma\" content=\"no-cache\" />\n"
			html += "<meta http-equiv=\"expires\" content=\"0\">\n"
			html += "</head>"
			html += f"Config-WebIF Access Deny ( IP: {IP} )<br>\n"
			html += "Please check Setting in Global > {}\n".format(_l(_("WebIF IP Allow")))
			html += "Default is: 127. 192.168. 172. 10.\n"
			html += "</body>\n"
			html += "</html>\n"
			return html.encode()
		if len(L1) == 0:
			ParseCode()
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')
		command = req.args.get(b"cmd")
		_command = command[0].decode() if command else ""
		ex = req.args.get(b"ex")
		_ex = ex[0].decode() if ex else None
		mo = req.args.get(b"Mode")
		el = req.args.get(b"Element")
		self.restartTimer()
		L4log(f"Command received '{command}', '{ex}'")
		if self.CurrentMode == ("-", "-"):
			self.CurrentMode = (getConfigStandby(), getisMediaPlayer())
		if mo:
			Mode = mo[0].decode()
			setConfigMode(True)
			if Mode in ["1", "2"]:
				setisMediaPlayer("")
				setConfigStandby(False)
			elif Mode == "3":
				setisMediaPlayer("config")
				setConfigStandby(False)
			elif Mode == "4":
				setisMediaPlayer("")
				setConfigStandby(True)
			elif Mode == "5":
				self.resetWeb()
			getBilder()
		html = ""
		if el:
			Element = el[0].decode()
		if req.args.get(b"save.y"):
			L4log("WebIF: save Config-File")
			LCD4linux.save()
			LCD4linux.saveToFile(LCD4config)
			ConfTimeCheck()
		if req.args.get(b"download.y"):
			L4log("WebIF: download Config")
			req.setResponseCode(http.OK)
			lcd4config = resolveFilename(SCOPE_CONFIG) + "lcd4config"
			return self.sendTextFile(req, 'attachment;filename=lcd4config', lcd4config)
		if req.args.get(b"upload.y"):
			L4log("WebIF: upload Config")
			lcd4config = "/tmp/test"
			data = req.args[b"uploadName"][0]
			if len(data) > 0 and data.startswith(b"config."):
				with open(lcd4config, "wb") as f:
					f.write(data)
				if isfile(lcd4config):
					L4LoadNewConfig(lcd4config)
			else:
				L4log("WebIF: Error upload")
				html += "<script language=\"JavaScript\">\n"
				html += "alert(\"{}\")\n".format(_("No or wrong File selected, try a correct File first !"))
				html += "</script>\n"
		if req.args.get(b"logdel.y"):
			L4log("WebIF: delete Logfile")
			rmFile("/tmp/L4log.txt")
		if req.args.get(b"logdownload.y"):
			L4log("WebIF: download Logfile")
			lcd4config = "/tmp/L4log.txt"
			if isfile(lcd4config):
				return self.sendTextFile(req, 'attachment;filename=l4log.txt', lcd4config)
		if command is None:
			L4logE("no command")
		elif _command == "exec" and ex:
			L4logE(f"exec: {_ex}")
			exec(_ex)
		elif _command == "enable":
			ExeMode = True
		elif _command == "status":
			StatusMode = True
		elif _command == "pop":
			V = _l(req.args.get(b"PopText", "")[0])
			try:
				V = _unescape(V)
			except Exception:
				L4log("WebIF Error: Parse Text")
			setPopText(V)
			L4LElement.setRefresh()
		elif _command == "popclear":
			setPopText("")
		elif _command.startswith("Screen"):
			setScreenActive(_command[-1])
			L4LElement.setRefresh()
		elif _command == "crashdel":
			rmFile(CrashFile)
		elif _command == "add" and ex:
			L4LElement.web(_ex)
		elif _command == "delete" and ex:
			L4LElement.delete(_ex)
		elif _command == "refresh":
			L4LElement.setRefresh()
		elif _command == "hold":
			setScreenActive("0")
			setSaveEventListChanged(not getSaveEventListChanged())
		elif _command == "screen" and ex:
			exs = _ex.split(",")
			if len(exs) == 1:
				L4LElement.setScreen(exs[0])
			elif len(exs) == 2:
				L4LElement.setScreen(exs[0], exs[1])
			elif len(exs) == 3:
				L4LElement.setScreen(exs[0], exs[1], exs[2] == "True")
		elif _command == "brightness" and ex:
			exs = _ex.split(",")
			if len(exs) == 1:
				L4LElement.setBrightness(exs[0])
			elif len(exs) == 2:
				L4LElement.setBrightness(exs[0], exs[1] == "True")
		elif _command == "getbrightness" and ex:
			if int(_ex) < 1 or int(_ex) > 3:
				return "0"
			else:
				return str(L4LElement.getBrightness(int(_ex)))
		elif _command == "getmjpeg" and ex:
			if int(_ex) < 1 or int(_ex) > 3:
				return "0"
			else:
				return str(getMJPEGreader(_ex))
		elif _command == "getexec" and ex:
			L4logE("getexec", _ex)
			_exec(f"getexec = {_ex}")
			return str(_ex)
		elif _command == "copyMP":
			for a in req.args.keys():
				_a = a.decode()
				if ".Standby" in _a:
					b = _a.replace(".Standby", ".MP")
					if (" " + b) in list(zip(*L3))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value
				elif "." in _a:
					b = _a.replace(".", ".MP")
					if (" " + b) in list(zip(*L3))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value
		elif _command == "copyIdle":
			for a in req.args.keys():
				_a = a.decode()
				if ".MP" in _a:
					b = _a.replace(".MP", ".Standby")
					if (" " + b) in list(zip(*L4))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value
				elif "." in _a:
					b = _a.replace(".", ".Standby")
					if (" " + b) in list(zip(*L4))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value
		elif _command == "copyOn":
			for a in req.args.keys():
				_a = a.decode()
				if ".MP" in _a:
					b = _a.replace(".MP", ".")
					if (" " + b) in list(zip(*L2))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value
				elif ".Standby" in _a:
					b = _a.replace(".Standby", ".")
					if (" " + b) in list(zip(*L2))[2]:
						obja = eval(a)
						objb = eval(b)
						objb.value = obja.value

#####################
# Konfig schreiben
#####################
		elif _command == "config":
			Cfritz = False
#			Cwetter = False
			Cpicon = False
			Ccal = False
			Cwww = False
			for a in req.args.keys():
				_a = a.decode()
				if _a.find(".") > 0:
					val = req.args.get(a, "")[0]
					val = val.decode()
					ConfObj = eval(_a)
					if isinstance(ConfObj, ConfigSelection):
						ConfObj.value = val
					elif isinstance(ConfObj, ConfigYesNo):
						val = req.args.get(a, "")
						ConfObj.value = True if len(val) == 2 else False
					elif isinstance(ConfObj, ConfigText):
						V = _l(val)
						try:
							V = _unescape(V)
						except Exception:
							L4log("WebIF Error: Parse Text")
						ConfObj.value = V
					elif isinstance(ConfObj, ConfigSlider):
						if val.isdigit():
							ConfObj.value = val
					elif isinstance(ConfObj, ConfigClock):
						t = val.split(":")
						if len(t) == 2 and t[0].isdigit() and t[1].isdigit():
							ConfObj.value = [int(t[0]), int(t[1])]
					if ConfObj.isChanged():
						ConfObj.save()
						L4log("Changed", a)
						if _a.find("Fritz") > 0:
							Cfritz = True
#						elif _a.find("Wetter") > 0:
#							Cwetter = True
						elif _a.find("Picon") > 0:
							Cpicon = True
						elif _a.find(".Cal") > 0 or _a.find(".MPCal") > 0 or _a.find(".StandbyCal") > 0:
							Ccal = True
						elif _a.find(".xmlType") > 0:
							if _a.find(".xmlLCDType") > 0:
								xmlRead()
								if xmlDelete(1) or xmlDelete(2) or xmlDelete(3):
									L4log("removed old Skindata")
									xmlWrite()
							if xmlSkin():
								xmlWrite()
								LCD4linuxConfigweb.RestartGUI = True
							xmlClear()
						elif _a.find(".MJPEG") > 0:
							MJPEG_stop("")
							MJPEG_start()
						elif _a.find(".Font") > 0:
							setFONT(LCD4linux.Font.value)
						if _a.find("WetterCity") > 0:
							LCD4linux.WetterCoords.value = "0,0"
							LCD4linux.WetterCoords.save()
							LCD4linux.saveToFile(LCD4config)
							resetWetter(0)
						if _a.find("Wetter2City") > 0:
							LCD4linux.Wetter2Coords.value = "0,0"
							LCD4linux.Wetter2Coords.save()
							LCD4linux.saveToFile(LCD4config)
							resetWetter(1)
						if _a.find("ScreenActive") > 0:
							setScreenActive(LCD4linux.ScreenActive.value)
						if _a.find("BildFile") > 0:
							getBilder()
						if _a.find("WWW1") > 0:
							if _a.find("WWW1url") > 0 or isfile(WWWpic % "1") is False:
								Cwww = True
							else:
								rmFile(WWWpic % "1p")
			if Cfritz:
				rmFile(PICfritz)
#			if Cwetter:
#				resetWetter(None)  # action after changing weather parameters
			if Cpicon:
				if len(LCD4linux.PiconCache.value) > 2:
					rmFiles(join(LCD4linux.PiconCache.value, "*.png"))
				if len(LCD4linux.Picon2Cache.value) > 2:
					rmFiles(join(LCD4linux.Picon2Cache.value, "*.png"))
			if Ccal:
				resetCal()
			if Cwww:
				getWWW()
			L4LElement.setRefresh()
#####################
# Anzeige
#####################
		html += "<html>"
		html += "<head>\n"
		html += "<meta http-equiv=\"Content-Language\" content=\"de\">\n"
		html += "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n"
		html += "<meta http-equiv=\"cache-control\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"pragma\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"expires\" content=\"0\">\n"
		html += "<link rel=\"shortcut icon\" href=\"/lcd4linux/data/favicon.png\">"
		if isfile(CrashFile):
			html += "<script language=\"JavaScript\">\n"
			html += "function fensterchen() {\n"
			html += "fens1=window.open(\"\", \"Crashlog\",\"width=500,height=300,resizable=yes\");\n"
			for line in open(CrashFile).readlines():
				html += "fens1.document.write('{}');\n".format(line.replace("\n", "<br>").replace("'", "\\'"))
			html += "} </script>\n"
		html += "<style type=\"text/css\">\n"
		html += ".style1 {\n"
		html += "vertical-align: middle; font-size:8px; }\n"
		html += "</style>\n"
		if L4LElement.getRefresh() is True:
			GI = getINFO().split()
			GR = min(int(float(GI[6])) + 1, 6) if len(GI) > 6 else 6
			html += f"<meta http-equiv=\"refresh\" content=\"{GR}\">\n"
		html += "<title>LCD4linux</title>\n"
		html += "</head>"
		html += "<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n"
		html += "<form method=\"POST\" action=\"--WEBBOT-SELF--\">\n"
		html += "</form>\n"
		html += "<table border=\"1\" rules=\"groups\" width=\"100%\" bordercolorlight=\"#000000\" bordercolordark=\"#000000\" cellspacing=\"0\">"
		html += "<tr><td bgcolor=\"#000000\" width=\"220\">\n"
		html += "<p align=\"center\"><img title=\"\" border=\"0\" src=\"/lcd4linux/data/WEBdreambox.png\" width=\"181\" height=\"10\">\n"
		CCM = "#FFFFFF" if getConfigMode() is False else "#FFCC00"
		html += (
			f"<font color=\"{CCM}\"><b>LCD4linux Config</b></font>"
			f"<br />{Version}\n"
		)
		if IP is None:
			html += "<br><span style=\"font-size:7pt;color: #FF0000\">{}!</span>".format(_l(_("IP seurity not supported by Box")))
		html += "</p></td><td bgcolor=\"#000000\">\n"
		html += "<p align=\"left\">"
		d = glob(f"{getTMPL()}dpf.*")
		if len(d) > 0:
			dpf1 = basename(d[0])
			html += (
				f"<a href=\"/lcd4linux\"><img style=\"color:#FFCC00\" title=\"LCD 1\" "
				f"src=\"/lcd4linux/{dpf1}?{time()}\" border=\"1\" height=\"80\" "
				f"id=\"reloader1\" "
				f"onload=\"setTimeout('document.getElementById(\\'reloader1\\').src=\\'/lcd4linux/{dpf1}?\\'+new Date().getTime()', 5000)\" ></a>"
			)
		d = glob(f"{getTMPL()}dpf2.*")
		if len(d) > 0:
			dpf2 = basename(d[0])
			html += (
				f"<a href=\"/lcd4linux?file={dpf2}\"><img style=\"color:#FFCC00\" "
				f"title=\"LCD 2\" src=\"/lcd4linux/{dpf2}?{time()}\" border=\"1\" "
				f"height=\"80\" id=\"reloader2\" "
				f"onload=\"setTimeout('document.getElementById(\\'reloader2\\').src=\\'/lcd4linux/{dpf2}?\\'+new Date().getTime()', 5000)\" ></a>"
			)
		d = glob(f"{getTMPL()}dpf3.*")
		if len(d) > 0:
			dpf3 = basename(d[0])
			html += (
				f"<a href=\"/lcd4linux?file={dpf3}\"><img style=\"color:#FFCC00\" "
				f"title=\"LCD 3\" src=\"/lcd4linux/{dpf3}?{time()}\" border=\"1\" "
				f"height=\"80\" id=\"reloader3\" "
				f"onload=\"setTimeout('document.getElementById(\\'reloader3\\').src=\\'/lcd4linux/{dpf3}?\\'+new Date().getTime()', 5000)\" ></a>"
			)
		html += "</p></td>\n"
		if isfile(CrashFile):
			html += "<td valign=\"top\" align=\"left\"  bgcolor=\"#000000\">\n"
			html += "<form method=\"post\"><font color=\"#FFFF00\">{}</font><br>\n".format(_l(_("Crashlog")))
			html += "<input type=\"hidden\" name=\"cmd\" value=\"\">\n"
			html += "<input type=\"button\" value=\"{}\" style=\"font-size:8pt;background-color:yellow;\" onClick=\"fensterchen()\">\n".format(_l(_("Show")))
			html += "<input type=\"button\" value=\"{}\" style=\"font-size:8pt;background-color:yellow;\"   onclick=\"this.form.cmd.value = 'crashdel'; this.form.submit();\">\n".format(_l(_("Delete")))
			html += "</form></td>\n"
		html += "<td valign=\"top\" align=\"right\"  bgcolor=\"#000000\">\n"
		html += "<form method=\"post\" enctype=\"multipart/form-data\">\n"
		html += "<input type=\"file\" name=\"uploadName\" title=\"{}\" class=\"style1\" >\n".format(_l(_("Filename")))
		html += "<input type=\"image\" name=\"upload\" value=\"klick\" src=\"/lcd4linux/data/WEBupload.png\" height=\"25\" title=\"{}\" class=\"style1\"  >\n".format(_l(_("Restore Config")))
		html += "<input type=\"image\" name=\"download\" value=\"klick\" src=\"/lcd4linux/data/WEBdownload.png\" height=\"25\" title=\"{}\" class=\"style1\" >\n".format(_l(_("Backup Config")))
		if isfile("/tmp/L4log.txt"):
			html += "<input type=\"image\" name=\"logdel\" value=\"klick\" src=\"/lcd4linux/data/WEBlogdel.png\" height=\"25\" title=\"{}\" class=\"style1\"  >\n".format(_l(_("Delete Logfile")))
			html += "<input type=\"image\" name=\"logdownload\" value=\"klick\" src=\"/lcd4linux/data/WEBlogshow.png\" height=\"25\" title=\"{}\" class=\"style1\" >\n".format(_l(_("Download Logfile")))
		html += "<input type=\"image\" name=\"save\" value=\"klick\" src=\"/lcd4linux/data/WEBsave.png\" height=\"40\" title=\"{}\" class=\"style1\" >\n".format(_l(_("Save Config")))
		html += "</form>\n"
		html += "<form method=\"post\"><font color=\"#FFFFFF\">{}</font>\n".format(_l(_("Screen")))
		html += "<input type=\"hidden\" name=\"cmd\" value=\"\">\n"
		for i in range(1, 10):
			html += (
				f"<input type=\"button\" value=\"{i}\" style=\"width:15px; text-align:center; font-size:8pt{AktiveScreen(str(i))}\" "
				f"onclick=\"this.form.cmd.value = 'Screen{i}'; this.form.submit();\">\n"
			)
		Aktiv = "checked" if getSaveEventListChanged() else ""
		html += "<input type=\"hidden\" name=\"hold\" value=\"{}\">".format("unchecked")
		html += "<input type=\"checkbox\" title=\"{}\" name=\"hold\" value=\"{}\" onclick=\"this.form.cmd.value = 'hold'; this.form.submit();\" {}>".format(_l(_("stop Screencycle")), "checked", Aktiv)
		html += "</form>\n"
		html += "</td></tr></table>\n"
		html += "<form method=\"get\">"
		html += "<fieldset style=\"width:auto\" name=\"Mode1\">"
		html += "<legend style=\"color: #FFCC00\">{}&nbsp;</legend>\n".format(_l(_("Mode")))
		html += "<input id=\"r1\" name=\"Mode\" type=\"radio\" value=\"1\" {} onclick=\"this.form.submit();\"><label {} for=\"r1\">{}&nbsp;&nbsp;</label>\n".format(*AktiveMode("1", _l(_("Global"))))
		html += "<input id=\"r2\" name=\"Mode\" type=\"radio\" value=\"2\" {} onclick=\"this.form.submit();\"><label {} for=\"r2\">{}&nbsp;&nbsp;</label>\n".format(*AktiveMode("2", _l(_("On"))))
		html += "<input id=\"r3\" name=\"Mode\" type=\"radio\" value=\"3\" {} onclick=\"this.form.submit();\"><label {} for=\"r3\">{}&nbsp;&nbsp;</label>\n".format(*AktiveMode("3", _l(_("Media"))))
		html += "<input id=\"r4\" name=\"Mode\" type=\"radio\" value=\"4\" {} onclick=\"this.form.submit();\"><label {} for=\"r4\">{}&nbsp;&nbsp;</label>\n".format(*AktiveMode("4", _l(_("Idle"))))
		if LCD4linuxConfigweb.RestartGUI is True:
			html += "<span style=\"color: #FF0000;\"><strong>{}</strong></span>".format(_l(_("GUI Restart is required")))
		if str(LCD4linux.Popup.value) != "0":
			html += "<input id=\"r5\" name=\"Mode\" type=\"radio\" value=\"5\" {} onclick=\"this.form.submit();\"><label {} for=\"r5\">{}&nbsp;&nbsp;</label>\n".format(*AktiveMode("5", "Popup-Text"))
		html += "</fieldset></form>\n"
		if Mode != "5":
			if Mode == "1":
				L = L1
			elif Mode == "2":
				L = L2
			elif Mode == "3":
				L = L3
			elif Mode == "4":
				L = L4
			else:
				Mode = "1"
				L = L1
				Element = "other"
			if str(LCD4linux.WebIfDesign.value) == "2":
				html += "<table border=\"0\"width=\"100%\" cellspacing=\"1\">"
				html += "<tr><td valign=\"top\" width=\"250\">"
			html += "<form method=\"get\">"
			html += "<fieldset style=\"width:auto\" name=\"Mode2\">"
			html += "<legend style=\"color: #FFCC00\">{}&nbsp;</legend>\n".format(_l(_("Element")))
			i = 0
			ElementList = []
			ElementText = ""
			for LL in L:
				Conf = LL[2].strip()
				if Mode == "1":
					Conf = Conf[:13]
				if ((not LL[1].startswith("-") and Mode != "1") or (Mode == "1" and Conf not in ElementList)) and int(LL[3]) != 0:
					if Element == "" or ModeOld != Mode:
						Element = "other"
						ModeOld = Mode
					ElementList.append(Conf)
					i += 1
					Ea, Ec = AktiveElement(Conf)
					if Mode != "1":
						ConfObj = eval(Conf)
						Curr = ConfObj.value
						L4log(f"Curr = {Conf}.value", Curr)
						if Curr != "0":
							Ec = "style=\"font-weight:bold;color:#CCFFBB\"" if Ec == "" else Ec.replace("=\"", "=\"font-weight:bold;")
					if Ea == "checked":
						ElementText = (_l(_(LL[1])) if Mode != "1" else _l(M[int(LL[3]) - 1]))
					html += f"<input id=\"e{i}\" name=\"Element\" type=\"radio\" value=\"{Conf}\" {Ea} onclick=\"this.form.submit();\"><label {Ec} for=\"e{i}\">{(_l(_(LL[1])) if Mode != '1' else _l(M[int(LL[3]) - 1]))}&nbsp;&nbsp;</label>\n"
					if str(LCD4linux.WebIfDesign.value) == "2":
						html += "<br>"
			Ea, Ec = AktiveElement("other")
			if Ea == "checked":
				ElementText = _l(_("other"))
			html += f"<input id=\"e0\" name=\"Element\" type=\"radio\" value=\"other\" {Ea} onclick=\"this.form.submit();\"><label {Ec} for=\"e0\">{_l(_('other'))}&nbsp;&nbsp;</label>\n"
			html += "</fieldset></form>\n"
			if str(LCD4linux.WebIfDesign.value) == "2":
				html += "<br></td><td valign=\"top\">"
			html += "<form name=\"Eingabe\" method=\"POST\">\n"
			if str(LCD4linux.WebIfDesign.value) == "2":
				html += f"<fieldset style=\"width:auto\" name=\"Mode3\"><legend style=\"color: #FFCC00\">{ElementText}&nbsp;</legend>"
			html += "<table border=\"1\" rules=\"groups\" width=\"100%\">"
			AktCode = 0
			isOn = False
			isMP = False
			isSb = False
			for LL in L:
				Conf = LL[2].strip()
				ConfObj = eval(Conf)
				if (Conf.startswith(Element) and (int(LL[3]) == AktCode or AktCode == 0)) or (Element == "other" and int(LL[3]) == 0):
					if Mode in "2":
						if "." in Conf:
							b = Conf.replace(".", ".MP")
							if (" " + b) in list(zip(*L3))[2]:
								isMP = True
							b = Conf.replace(".", ".Standby")
							if (" " + b) in list(zip(*L4))[2]:
								isSb = True
					elif Mode in "3":
						if ".MP" in Conf:
							b = Conf.replace(".MP", ".")
							if (" " + b) in list(zip(*L2))[2]:
								isOn = True
							b = Conf.replace(".MP", ".Standby")
							if (" " + b) in list(zip(*L4))[2]:
								isSb = True
					elif Mode in "4" and ".Standby" in Conf:
						b = Conf.replace(".Standby", ".")
						if (" " + b) in list(zip(*L2))[2]:
							isOn = True
						b = Conf.replace(".Standby", ".MP")
						if (" " + b) in list(zip(*L3))[2]:
							isMP = True
					if AktCode == 0:
						AktCode = int(LL[3])
					Curr = ConfObj.value
					html += "<tr>\n"
					if isinstance(ConfObj, ConfigSelection):
						html += f"<td width=\"300\">{_l(_(LL[1]))}</td><td>\n"
						html += f"<select name=\"{Conf}\" size=\"1\">\n"
						Len = len(ConfObj.description)
						for i in list(range(Len)):
							Choice = ConfObj.choices[i]
							Wert = ConfObj.description[Choice]
							Aktiv = " selected" if str(Choice) == str(Curr) else ""
							html += f"<option value=\"{Choice}\" {Aktiv}>{_l(Wert)}</option>\n"
						html += "</select>\n"
						html += "</td>\n"
					elif isinstance(ConfObj, ConfigYesNo):
						html += f"<td width=\"300\">{_l(_(LL[1]))}</td><td>\n"
						Aktiv = "checked" if Curr else ""
						html += "<input type=\"hidden\" name=\"{}\" value=\"{}\">".format(Conf, "unchecked")
						html += "<input type=\"checkbox\" name=\"{}\" value=\"{}\" {}>".format(Conf, "checked", Aktiv)
						html += "</td>\n"
					elif isinstance(ConfObj, ConfigText):
						html += f"<td width=\"300\">{_l(_(LL[1]))}</td><td>\n"
						html += f"<input type=\"password\" name=\"{Conf}\" size=\"60\" value=\"{_l(Curr)}\">" if isinstance(ConfObj, ConfigPassword) else f"<input type=\"text\" name=\"{Conf}\" size=\"60\" value=\"{_l(Curr)}\">"
						html += "</td>\n"
					elif isinstance(ConfObj, ConfigSlider):
						Min = ConfObj.min
						Max = ConfObj.max
						html += f"<td width=\"300\">{_l(_(LL[1]))} ({Min} - {Max})</td><td>\n"
						html += f"<input type=\"text\" name=\"{Conf}\" size=\"5\" value=\"{Curr}\">"
						html += "</td>\n"
					elif isinstance(ConfObj, ConfigClock):
						html += f"<td width=\"300\">{_l(_(LL[1]))}</td><td>\n"
						html += f'<input type="text" name="{Conf}" size="6" value="{Curr[0]:02d}:{Curr[1]:02d}">'
						html += "</td>\n"
			html += "</tr></table>\n"
			html += "<input type=\"hidden\" name=\"cmd\" value=\"config\">\n"
			html += "<input type=\"submit\" style=\"background-color: #FFCC00\" value=\"{}\">\n".format(_l(_("set Settings")))
			if Element != "other":
				if Mode in ["3", "4"] and isOn:
					html += "<input type=\"button\" align=\"middle\" style=\"text-align:center; font-size:8pt\" value=\"{}\" onclick=\"this.form.cmd.value = 'copyOn'; this.form.submit(); \">\n".format(_l(_("copy to On")))
				if Mode in ["2", "4"] and isMP:
					html += "<input type=\"button\" align=\"middle\" style=\"text-align:center; font-size:8pt\" value=\"{}\" onclick=\"this.form.cmd.value = 'copyMP'; this.form.submit(); \">\n".format(_l(_("copy to Media")))
				if Mode in ["2", "3"] and isSb:
					html += "<input type=\"button\" align=\"middle\" style=\"text-align:center; font-size:8pt\" value=\"{}\" onclick=\"this.form.cmd.value = 'copyIdle'; this.form.submit(); \">\n".format(_l(_("copy to Idle")))
			html += "</fieldset></td></tr></table>" if str(LCD4linux.WebIfDesign.value) == "2" else "</form>\n"
		elif Mode == "5":
			html += "<form method=\"POST\">\n"
			html += "<fieldset style=\"width:auto\" name=\"Mode2\">\n"
			html += f"<textarea name=\"PopText\" style=\"height: 120px; width: 416px\">{_l(PopText[1])}</textarea>"
			html += "<input type=\"hidden\" name=\"cmd\" value=\"pop\">\n"
			html += "<input type=\"submit\" style=\"background-color: #FFCC00\" value=\"{}\">\n".format(_l(_("set Settings")))
			html += "</fieldset></form>\n"
		if ExeMode is True:
			html += "<br />\n"
			html += "<form method=\"GET\">\n"
			html += "<input type=\"hidden\" name=\"cmd\" value=\"exec\">\n"
			html += "<input style=\"width: 400px\" type=\"text\" name=\"ex\">\n"
			html += "<input type=\"submit\" value=\"{}\">\n".format(_l(_("Exec")))
			html += "</form>\n"
		if StatusMode is True:
			html += "<br />\n"
			html += f"Screen: {str(getScreenActive(True))}<br />\n"
			html += f"Hold/HoldKey: {str(getSaveEventListChanged())}/{str(L4LElement.getHoldKey())}<br />\n"
			html += f"Brightness org/set {str(L4LElement.getBrightness())}/{str(L4LElement.getBrightness(0, False))}<br />\n"
		html += f"<hr><span style=\"font-size:8pt\">{getINFO()} ({IP})</span>"
		html += "<BR><a style=\"font-size:10pt; color:#FFCC00;\" href=\"https://www.opena.tv/viewtopic.php?t=73\">Support & FAQ & Info & Donation</a>"
		if len(L4LElement.get()) > 0:
			html += "<script language=\"JavaScript\">\n"
			html += "function Efensterchen() {\n"
			html += "fens1=window.open(\"\", \"Externals\",\"width=500,height=300,resizable=yes\");\n"
			L4Lkeys = sorted(L4LElement.get().keys())
			for CUR in L4Lkeys:
				html += "fens1.document.write('{} {}<BR>');\n".format(CUR, str(L4LElement.get(CUR)).replace("\n", "<br>").replace("'", "\\'"))
			html += "} </script>\n"
			html += "<form method=\"post\"><br>\n"
			html += "<input type=\"button\" value=\"{}\" style=\"font-size:8pt;\" onClick=\"Efensterchen()\">\n".format(_l(_("Show Externals")))
			html += "</form></td>\n"
		html += "</body>\n"
		html += "</html>\n"
		return html.encode()
