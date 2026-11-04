from os import stat, symlink
from os.path import isfile
from enigma import ePixmap, eTimer
from Components.Renderer.Renderer import Renderer


class PixmapLcd4linux(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.mTime = 0
		self.swap = False
		self.L4Ltimer = eTimer()
		self.L4Ltimer.callback.append(self.changed)

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		self.changed((self.CHANGED_DEFAULT,))

	def onShow(self):
		Renderer.onShow(self)
		self.changed((self.CHANGED_DEFAULT,))

	def onHide(self):
		Renderer.onHide(self)
		self.L4Ltimer.stop()

	def changed(self, *args):
		self.L4Ltimer.stop()
		if isfile("/tmp/l4ldisplay.png"):
			try:
				mtime = stat("/tmp/l4ldisplay.png").st_mtime
				if self.mTime != mtime:
					if self.instance:
						if self.swap:
							if not isfile("/tmp/l4ldisplaycp.png"):
								symlink("/tmp/l4ldisplay.png", "/tmp/l4ldisplaycp.png")
							self.instance.setPixmapFromFile("/tmp/l4ldisplaycp.png")
						else:
							self.instance.setPixmapFromFile("/tmp/l4ldisplay.png")
						self.mTime = mtime
						self.swap = not self.swap
					else:
						self.mTime = 0
			except OSError:
				pass
		if not self.suspended:  # Keep polling while visible, even if the picture does not exist yet.
			self.L4Ltimer.start(200, True)
