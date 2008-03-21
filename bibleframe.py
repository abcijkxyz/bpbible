import random

import wx

from swlib.pysw import VK, GetVerseStr, GetBookChapter, GetBestRange
from bookframe import VerseKeyedFrame
from displayframe import IN_BOTH, IN_MENU, IN_POPUP
from gui.htmlbase import linkiter, eq
from util.util import ReplaceUnicode
from gui import guiutil
from util.observerlist import ObserverList

import config, guiconfig
from gui.menu import MenuItem, Separator

from harmony.harmonyframe import HarmonyFrame
from gui.quickselector import QuickSelector
from events import BIBLEFRAME, RANDOM_VERSE, VERSE_LINK_SELECTED
from copyverses import CopyVerseDialog

from util.configmgr import config_manager
from versecompare import VerseCompareFrame


bible_settings = config_manager.add_section("Bible")
bible_settings.add_item("verse_per_line", False, item_type=bool)


class BibleFrame(VerseKeyedFrame):
	title = "Bible"

	def setup(self):
		self.observers = ObserverList()
		super(BibleFrame, self).setup()
	
	def get_menu_items(self):
		items = super(BibleFrame, self).get_menu_items()
		items = (
			(MenuItem("Harmony", self.show_harmony, accelerator="Ctrl-H"),
				IN_MENU),
			(MenuItem("Random verse", self.random_verse, accelerator="Ctrl-R"),
				IN_BOTH),
			(MenuItem("Copy verses", guiconfig.mainfrm.on_copy_button, 
				enabled=self.has_module, accelerator="Ctrl-Alt-C"), IN_BOTH),
			
			(MenuItem("Open sticky tooltip", self.open_sticky_tooltip, 
					enabled=self.has_module), IN_POPUP),
					
			(MenuItem("Compare verses", self.compare_verses, 
					enabled=self.has_module), IN_POPUP),
					
			
			(Separator, IN_BOTH),
			(MenuItem("Search", self.search, accelerator="Ctrl-F"), IN_MENU),
			(Separator, IN_MENU),
				 
		) + items

		return items
	
	def get_actions(self):
		actions = super(BibleFrame, self).get_actions()
		actions.update({
			ord("S"): self.search_quickly,
			(ord("C"), wx.MOD_CMD|wx.MOD_SHIFT): self.copy_quickly,
			(ord("T"), wx.MOD_SHIFT): self.tooltip_quickly,
			
		})
		return actions
	
	def tooltip_quickly(self):
		qs = QuickSelector(self.get_window(), 
			title="Open sticky tooltip")

		qs.pseudo_modal(self.tooltip_quickly_finished)
		
	def tooltip_quickly_finished(self, qs, ansa):
		if ansa == wx.OK:
			text = self.get_verified_multi_verses(qs.text)
			if text:
				self.open_tooltip(text)
				
		qs.Destroy()
	
	
	def get_quick_selected(self):
		text = self.GetRangeSelected()

		if not text:
			text = self.reference

		return text

	def open_sticky_tooltip(self):
		"""Open a sticky tooltip with the selected verses"""
		text = self.get_quick_selected()
		self.open_tooltip(text)
	
	
	def compare_verses(self):
		"""Open the verse comparison pane to the selected verses"""
		
		text = self.get_quick_selected()
		title = VerseCompareFrame.title
		#if not guiconfig.mainfrm.is_pane_shown(title):
		guiconfig.mainfrm.show_panel(title)
		guiconfig.mainfrm.verse_compare.notify(text)
			
	
	def copy_quickly(self):
		text = self.get_quick_selected()
		
		cvd = CopyVerseDialog(self)
		cvd.copy_verses(text)
		cvd.Destroy()	
	
		
	def show_harmony(self):
		"""Opens the harmony"""
		harmony_frame = HarmonyFrame(guiconfig.mainfrm)
		harmony_frame.SetIcons(guiconfig.icons)
		harmony_frame.Show()
		
	def search(self):
		"""Search in this bible"""
		guiconfig.mainfrm.search_panel.show()
	
	def update_title(self, shown=None):
		m = guiconfig.mainfrm
		p = m.get_pane_for_frame(self)
		version = self.book.version
		ref = self.reference
		text = "%s (%s)" % (ref, version)
		m.set_pane_title(p.name, text)		
		
	
	def random_verse(self):
		"""Go to a random verse"""
		randomnum = random.randint(1, 31102)
		text = VK("Gen 1:"+str(randomnum)).text
		self.notify(text, source=RANDOM_VERSE)
	
	def notify(self, reference, source=BIBLEFRAME):
		#event = BibleEvent(ref=reference, source=source)
		self.observers(reference, source)

	def search_quickly(self):
		qs = QuickSelector(self.get_window(), 
			title="Search in Bible for:")

		qs.pseudo_modal(self.search_quickly_finished)
	
	def search_quickly_finished(self, qs, ansa):
		if ansa == wx.OK:
			guiconfig.mainfrm.search_panel.search_and_show(qs.text)

		qs.Destroy()
	
	@guiutil.frozen
	def SetReference(self, ref, context=None, raw=None):
		"""Sets reference. This is set up to be an observer of the main frame,
		so don't call internally. To set verse reference, use notify"""
		if raw is None:
			raw = config.raw

		self.reference = GetVerseStr(ref)

		chapter = GetBookChapter(self.reference)
		data = '<table width="100%" VALIGN=CENTER ><tr>'
		vk = VK(self.reference)
		vk.chapter -= 1
		d = lambda:{"ref":GetBookChapter(vk.text),
				"graphics":config.graphics_path}

		if not vk.Error():
			data += ('<td align="LEFT" valign=CENTER>'
					 '<a href="nbible:%(ref)s">'
					 '<img src="%(graphics)sgo-previous.png">&nbsp;'
					 '%(ref)s</a></td>'
			) % d()
		else:
			data += '<td align=LEFT>'+ '&nbsp;'*15 + '</td>'
					

		data += "<td align=CENTER><center>%s</center></td>" % \
				"<h3>%s</h3>" % chapter
		
		vk = VK(self.reference)
		vk.chapter += 1
		if not vk.Error():
			data += ('<td align="RIGHT" valign=CENTER>'
					 '<a href="nbible:%(ref)s">%(ref)s&nbsp;'
					 '<img src="%(graphics)sgo-next.png">'
					 '</a></td>'
			) % d()
		else:
			data += '<td align=RIGHT>'+ '&nbsp;'*15 + '</td>'

		data += "</tr></table>\n"

		chapter = self.book.GetChapter(ref, self.reference,
			config.current_verse_template, context, raw=raw)

		if chapter is None:
			data = config.MODULE_MISSING_STRING
			self.SetPage(data, raw=raw)
			
			

		else:
			data += chapter

			data = data.replace("<!P>","</p><p>")
			if not wx.USE_UNICODE:
				#replace common values
				data = ReplaceUnicode(data)

			self.SetPage(data, raw=raw)

			#set to current verse
			self.scroll_to_current()

		#file = open("a.html","w")
		#file.writelines(data)
		#file.close()
		self.update_title()
		
		
	def scroll_to_current(self):
		me = self.Find(self.GetInternalRepresentation(), "#current")
		self.ScrollTo("current", me)
		
	
	def Find(self, cell, linktext):
		"""Find anchor in hierarchy. 
		
		This is used instead of	html.HtmlCell.Find, which doesn't work as it
		expects a 'void *'"""
		child = cell.GetFirstChild()
		while child:
			ret = self.Find(child, linktext)
			if(ret):
				return ret
			child = child.GetNext()
		link = cell.GetLink()
		if(not link):
			return
		if(str(link.GetHref())==str(linktext)):
			return cell

	def ScrollTo(self, anchor, c):
		#register change
		
		# this used to be here...
		#    self.ScrollToAnchor(anchor)


		#scroll up a bit if possible
		#this is the start
		#x, y = self.GetViewStart()
		#multiply to get pixels
		#xx, yy = self.GetScrollPixelsPerUnit()
		#y* = yy
		# y = start in pixels 
		# take 50 off y only if not within 100 pxls of bottom
		#X, Y = self.GetVirtualSize()
		# Y = Virtual size
		#width, height = self.GetClientSizeTuple()
		# client height - height
		# y + height = bottom of screen (or should)
		# y = start of view
		# h = height of view
		# if start + height is less than 100 from Virtual Size
		# don't scroll
		# if more than 100 pixels, do
		#if(Y-y>50): 
		#	y- = 100
	#	
	#	if y < 0: y = 0
	#	#convert back
	#	y/ = yy
	#	#scroll
	#	self.Scroll(x, y)
		y = 0
		scrollstep = self.GetScrollPixelsPerUnit()[1]

		while c:
			y+=c.GetPosY()
			c = c.GetParent()
		height = self.GetClientSizeTuple()[1]
		#if(y>=50 and y<150):
		#	pass#y- = (y-100)
		#else:
		#	y- = 100
		# Try and keep in middle
		# -40 is to correct for verse length, as we do not want start of 
		# verse to start half way down, but the middle to be in the middle
		median = height/2-40
		if(y<median):
			y = 0
		else:
			y -= median

		self.Scroll(-1, y/scrollstep)
		


	def LinkClicked(self, link, cell):
		if(self.select): return
		#cell = link.GetHtmlCell()
		href = str(link.GetHref())
		if(href.startswith("#")):
			string = cell.ConvertToText(None)
			self.notify(GetVerseStr(string, self.reference),
				source=VERSE_LINK_SELECTED)
			#self.ScrollTo(string,cell)
			return
		super(BibleFrame, self).LinkClicked(link, cell)
	
	def FindVerse(self, cell):
		assert cell.IsTerminalCell()
		i = linkiter(self.GetInternalRepresentation().GetFirstChild(), cell)

		prev = i.m_pos
		verse = None
		while (i):
			#print cell, i.m_pos
		
			# new block
			#if (not eq(prev.GetParent(), i.m_pos.GetParent())):
			#	text += '\n';
			#	faketext += '\n'
			#print i.m_pos.ConvertToText(None)

			if(i.m_pos.GetLink()):
				target = i.m_pos.GetLink().GetTarget()
				if target:
					try:
						int(target)
					except:
						print "Excepting"
						pass
					else:
						verse = target
						#print "TARGET", target

			
			prev = i.m_pos
			i.next()
			

		if not eq(prev, cell):
			return None

		if not verse:
			return None

		return GetVerseStr(verse, self.reference)
	
	def GetRangeSelected(self):
		if not self.m_selection:
			return

		self.first = self.m_selection.GetFromCell()
		self.last = self.m_selection.GetToCell()

		first = self.FindVerse(self.first)
		last = self.FindVerse(self.last)

		if not first:
			first = GetVerseStr("1", self.reference)

		if not last:
			return ""

		text = first + " - " + last
		return GetBestRange(text)

	
	def CellClicked(self, cell, x, y, event):
		#if(self.select): return
		if(event.ControlDown()):
			print cell.this, self.FindVerse(cell)

		return super(BibleFrame, self).CellClicked(cell, x, y, event)

