from urllib.request import urlopen
from xml.etree.ElementTree import fromstring


def parseXmlToJson(xml):
	return {x.tag: parseXmlToJson(x) if len(x) > 0 else (x.text or "") for x in xml}


class BlueSound:
	def __init__(self, ip):
		self.IP = ip
		self.baseUrl = f"http://{ip}:11000/"  # NOSONAR - lokale BluOS-API bietet kein HTTPS

	def urlGet(self, url):
		f = urlopen(url, timeout=1)
		fr = f.read()
		fc = f.code
		f.close()
		return (fr, fc)

	def getStatus(self):
		result = {}
		try:
			content, resp = self.urlGet(f"{self.baseUrl}Status")
			if resp == 200:
				result = parseXmlToJson(fromstring(content))
		except Exception:
			print("Bluesound Error")
			from traceback import format_exc
			print(f"Error: {format_exc()}")
		return result
