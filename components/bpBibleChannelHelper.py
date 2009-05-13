import xpcom
from backend.bibleinterface import biblemgr
from swlib.pysw import SW
import os
import config

class bpBibleChannelHelper:
	_com_interfaces_ = xpcom.components.interfaces.bpBibleChannelHelper
	_reg_clsid_ = "b79e8f5b-5aee-47e2-b831-d3a2f7609549"
	_reg_contractid_ = "@bpbible.com/bpBibleChannelHelper;1"

	def getDocument( self, param0 ):
		import time
		t = time.time()

		# Result: wstring
		# In: param0: wstring
		print "PARAM0", param0, 
		
		ref = SW.URL.decode(param0).c_str()[1:]
		assert "!" not in ref

		print `ref`
		if not ref: return "<html><body>Content not loaded</body></html>"
		print "Ref contains '!'?", "!" in ref
		r = ref.rfind("#")
		if r != -1:
			ref = ref[:r]

		print ref

		c = biblemgr.bible.GetChapter(ref, ref, config.current_verse_template)
		c = c.replace("<!P>", "&lt;!P&gt;")
		stylesheet = '<link rel="stylesheet" type="text/css" href="about:bpcss"/ >'
		if "bpbibleng" in os.getcwd():
			p = os.path.expanduser("~/bpbibleng/chrome/skin/standard/bpbible_html.css")
			#s = open().read()
			#stylesheet = "<style type='text/css'>%s</style>" % s
			stylesheet += '<link rel="stylesheet" type="text/css" href="file:///%s" />' % p
			

		text = '''\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" 
                      "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	%s
	<script type="text/javascript" src="about:bpjq"></script>
	<script type="text/javascript" src="about:bpjs"></script>	
</head>
<body>
	<!-- <p> -->
	%s
	<!-- </p> -->
	%s
</body></html>''' % (stylesheet, c, 
	"<div class='timer'>Time taken: %.3f</div>" % (time.time() - t))
		
		try:
			open("tmp.html", "w").write(text)
		except Exception, e:
			print "Error writing", e
		return text
		return u"test. And param0 was %s" % param0
