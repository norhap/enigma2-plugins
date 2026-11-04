from json import loads
from urllib.request import urlopen


class YMC:
	def __init__(self, ip):
		self.IP = ip
		self.L4logE = L4logE

	def urlGet(self, url):
		f = urlopen(url, timeout=1)
		fr = f.read()
		fc = f.code
		f.close()
		return (fr, fc)

	def getPlayInfo(self):
		try:
			content, resp = self.urlGet(f"http://{self.IP}/YamahaExtendedControl/v1/netusb/getPlayInfo")  # NOSONAR - lokale Yamaha-API bietet kein HTTPS
			return loads(content) if resp == 200 else {}

		except Exception as e:
			self.L4logE(f"YMC Error: {e}")
			return {}

	def getStatus(self):
		try:
			content, resp = self.urlGet(f"http://{self.IP}/YamahaExtendedControl/v1/main/getStatus")  # NOSONAR - lokale Yamaha-API bietet kein HTTPS
			return loads(content) if resp == 200 else {}
		except Exception as e:
			self.L4logE(f"YMC Error: {e}")
			return {}
