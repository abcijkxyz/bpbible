"""
Methods that used to live on frames; these may be moved in the future
"""

from backend.bibleinterface import biblemgr
from contrib.jsproxy import JSProxy
from protocol_handlers import TooltipConfigHandler
def _get_modulename(window):
	return window.content.document.body.getAttribute("module")

def get_module_for_frame(window):
	return biblemgr.modules[_get_modulename(window)]

def get_book_for_frame(window):
	return biblemgr.get_module_book_wrapper(_get_modulename(window))

import weakref
window_timer = weakref.WeakKeyDictionary()
firer = None
def clear_tooltip(window):
	if window in window_timer:
		window.clearTimeout(window_timer[window])
	
def show_tooltip(window, config):
	t = window.setTimeout(300, _show_tooltip, window, config)
	clear_tooltip(window)
	window_timer[window] = t

def _show_tooltip(window, config):
	tt = window.document.getElementById("tooltippanel")
	assert tt
	tt.removeAttribute("hidden")
	if tt.firstChild:
		tt.removeChild(tt.firstChild)

	if not tt.firstChild:
		print "Creating iframe"
		inner = window.document.createElement("browser")
		inner.setAttribute("tooltip", "aHTMLTooltip")
		inner.setAttribute("disablehistory", "true")
		#inner.setAttribute("src", "chrome://bpbible/content/tooltip.xul")
		inner.setAttribute("flex", "1")
		tt.appendChild(inner)

		#panel = window.document.createElement("tooltip")
		#panel.setAttribute()
		#tt.appendChild(panel)

	path = TooltipConfigHandler.register(config)
	tt.firstChild.setAttribute("src", path)
	#inner = JSProxy(tt.firstChild).contentWindow
	#print inner.content.location.href
	#print inner.location.href
	#inner.content.location.href = "data:,test"
	p = JSProxy(tt)
	p.hidePopup()
	p.sizeTo(300, 300)
	p.openPopup(firer, "after_start", 1, 1, False, False)

