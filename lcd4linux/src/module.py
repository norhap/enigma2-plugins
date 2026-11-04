# by joergm6 @ IHAD
# for documentation look at IHAD Support Thread

from subprocess import getstatusoutput
from os.path import isfile, exists


class L4Lelement:
	List = {}
	Refresh = False
	MAX_W = [0, 0, 0]
	MAX_H = [0, 0, 0]
	Bright = [-1, -1, -1]
	BrightAkt = [0, 0, 0]
	Screen = ""
	LCD = ""
	Hold = False
	HoldKey = False
	Font = ["", "", "", ""]
	Version = False

	def __init__(self):
		self.session = None

	def add(self, element, para):
		print(f"[LCD4linuxE] Add: {element} {para}")
		if "%" in para.get("Align", ""):
			para["Align"] = ("0000" + para["Align"].replace("%", "00"))[-4:]
		if para.get("Value") is not None:
			para["Value"] = min(max(int(para["Value"]), 0), 100)
		L4Lelement.List[element] = para

	def delete(self, element):
		print(f"[LCD4linuxE] Del: {element}")
		if L4Lelement.List.get(element) is not None:
			del L4Lelement.List[element]
		else:
			for x in list(L4Lelement.List):
				if x.startswith(element):
					del L4Lelement.List[x]

	def show(self):
		print(L4Lelement.List)

	def get(self, element=None):
		return L4Lelement.List if element is None else L4Lelement.List.get(element, {})

	def web(self, EX):
		try:
			args = EX.replace(",", "',", 1)
			exec(f"self.add('{args})")
		except Exception:
			print("[LCD4linuxE] Error: L4L Web-Elements")

	def getResolution(self, LCD):
		if int(LCD) < 1 or int(LCD) > 3:
			return 0, 0
		return L4Lelement.MAX_W[int(LCD) - 1], L4Lelement.MAX_H[int(LCD) - 1]

	def setResolution(self, LCD, MW, MH):
		L4Lelement.MAX_W[int(LCD) - 1] = int(MW)
		L4Lelement.MAX_H[int(LCD) - 1] = int(MH)

	def resetRefresh(self):
		L4Lelement.Refresh = False

	def setRefresh(self):
		L4Lelement.Refresh = True

	def getRefresh(self):
		return L4Lelement.Refresh

	def getHold(self):
		return L4Lelement.Hold

	def setHold(self, H):
		print(f"[LCD4linuxE] hold: {H}")
		L4Lelement.Hold = H

	def getHoldKey(self):
		return L4Lelement.HoldKey

	def setHoldKey(self, H=False):
		print(f"[LCD4linuxE] holdkey: {H}")
		L4Lelement.HoldKey = H

	def getFont(self, F="0"):
		if L4Lelement.Font[int(F)].endswith(".ttf") and isfile(L4Lelement.Font[int(F)]):
			return L4Lelement.Font[int(F)]
		else:
			return L4Lelement.Font[0]

	def setFont(self, F):
		L4Lelement.Font = F

	def getScreen(self):
		return L4Lelement.Screen

	def setScreen(self, S, Lcd="", Hold=False):
		if Lcd != "" and (len(str(Lcd)) > 1 or int(Lcd) > 3):
			Lcd = "1"
		L4Lelement.Screen = str(S)
		L4Lelement.LCD = str(Lcd)
		L4Lelement.Hold = Hold
		L4Lelement.Refresh = True

	def resetBrightness(self, AKT=[]):
		if len(AKT) == 3:
			L4Lelement.BrightAkt = AKT
		else:
			L4Lelement.Bright = [-1, -1, -1]

	def setBrightness(self, LCD, BRI=-1):
		if int(LCD) > 0 and int(LCD) < 4:
			L4Lelement.Bright[int(LCD) - 1] = int(BRI)
			L4Lelement.Refresh = True

	def getBrightness(self, LCD=0, ORG=True):
		if int(LCD) > 0 and int(LCD) < 4:
			return [L4Lelement.Bright[int(LCD) - 1]] if ORG == False else [L4Lelement.BrightAkt[int(LCD) - 1]]
		else:
			return L4Lelement.Bright if ORG == False else L4Lelement.BrightAkt

	def getLcd(self):
		return L4Lelement.LCD

	def setVersion(self, V):
		L4Lelement.Version = L4LVtest(V)

	def getVersion(self):
		return L4Lelement.Version


def getStatusOutput(cmd):
	try:
		return getstatusoutput(cmd)
	except Exception as exc:
		print(f"[LCD4linux] Error on system call: {exc}")
		return 1, "- -"


def L4LVtest(VV):
	L4Linfo = "/%s/lib/%s/info/enigma2-plugin-extensions-lcd4linux.control"
	OX = ""
	OO = False
	P = "opkg"
	if exists(L4Linfo % ("var", "opkg")):
		OX = "var"
	elif exists(L4Linfo % ("var", "dpkg")):
		OX = "var"
		P = "dpkg"
	elif exists("/var/lib/dpkg/status"):
		(r1, r2) = getStatusOutput("dpkg -s enigma2-plugin-extensions-lcd4linux | grep Version")
		if r1 == 0:
			OO = r2.strip().split()[1].startswith(VV[1:])
	if OX != "":
		try:
			with open(L4Linfo % (OX, P)) as file:
				OO = file.readline().strip().split()[1].startswith(VV[1:])
		except Exception:
			pass
	return OO
