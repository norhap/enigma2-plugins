from os.path import isfile, getmtime
from twisted.web import resource
from .plugin import getConfigMode, getTMPL, LCD4linux


class LCD4linuxweb(resource.Resource):
	title = "LCD4Linux Webinterface"
	isLeaf = False

	def __init__(self):
		self.HREF = "href=\"/lcd4linux/config\""

	def getRefreshMarkup(self):
		webIfType = LCD4linux.WebIfType.value
		if webIfType == "1":
			result = (f"<meta http-equiv=\"refresh\" content=\"{LCD4linux.WebIfRefresh.value}\">\n", "")
		else:  # "0" = Javascript with page reload, "01" = Javascript without page reload
			refreshMeta = "<meta http-equiv=\"refresh\" content=\"300\">\n" if webIfType == "0" else ""
			result = (refreshMeta, " id=\"reloader{index}\" onload=\"setTimeout('document.getElementById(\\'reloader{index}\\').src=\\'/lcd4linux/{image}?\\'+new Date().getTime()', {delay})\"")
		return result

	def renderPicture(self, filename, index, attributes, javaRefresh):
		mtime = int(getmtime(f"{getTMPL()}{filename}"))
		jr = javaRefresh.format(index=index, image=filename, delay=int(LCD4linux.WebIfRefresh.value) * 1000) if javaRefresh else ""
		return f"<a {self.HREF}><img border=\"0\" src=\"/lcd4linux/{filename}?{mtime}\" {jr} {attributes}></a> \n"

	def render(self, request):
		request.setHeader('Content-type', 'text/html')
		request.setHeader('charset', 'UTF-8')
# rendering server response
		attributes = ""
		command = request.args.get(b"width", None)
		if command is not None:
			cmd = command[0].decode()
			attributes += f" width=\"{cmd}\""
		command = request.args.get(b"hight", None)
		if command is not None:
			cmd = command[0].decode()
			attributes += f" height=\"{cmd}\""
		html = (
			"<html>"
			"<head>\n"
			"<meta http-equiv=\"Content-Language\" content=\"de\">\n"
			"<meta http-equiv=\"Content-Type\" content=\"text/html; charset=windows-1252\">\n"
			"<meta http-equiv=\"cache-control\" content=\"no-cache\" />\n"
			"<meta http-equiv=\"pragma\" content=\"no-cache\" />\n"
			"<meta http-equiv=\"expires\" content=\"0\">\n"
			"<link rel=\"shortcut icon\" href=\"/lcd4linux/data/favicon.png\">"
		)
		refreshMeta, javaRefresh = self.getRefreshMarkup()
		html += refreshMeta
		html += "<title>LCD4linux</title>\n"
		html += "</head>"
		html += f"<body bgcolor=\"{'#666666' if getConfigMode() is True else '#000000'}\" text=\"#FFFFFF\">\n"
		html += "<form method=\"POST\" action=\"--WEBBOT-SELF--\">\n"
		requestedFile = request.args.get(b"file", None)
		if requestedFile is not None:
			requestedFile = [item.decode("utf-8") for item in requestedFile]
			if requestedFile and isfile(f"{getTMPL()}{requestedFile[0]}"):
				html += self.renderPicture(requestedFile[0], 1, attributes, javaRefresh)
		else:
			for index, filename in enumerate([
				"dpf.jpg",
				"dpf.png",
				"dpf2.jpg",
				"dpf2.png",
				"dpf3.jpg",
				"dpf3.png",
			], start=2):
				if isfile(f"{getTMPL()}{filename}"):
					html += self.renderPicture(filename, index, attributes, javaRefresh)
					break
			else:
				html += f"<a style=\"color:#FFCC00\" {self.HREF}>no Picture .... Config-WebIF</a>"
		html += "</body>\n"
		html += "</html>\n"
		html += "</form>\n"
		return html.encode()


class LCD4linuxwebView(LCD4linuxweb):
	def __init__(self):
		self.HREF = ""
