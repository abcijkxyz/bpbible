from xrc.module_manager_xrc import xrcModuleManagerDialog
from module_tree import PathModuleTree
from backend.bibleinterface import biblemgr
from backend import book

from swlib.pysw import SW
import wx
from swlib.installmgr import InstallMgr

class ModuleManagerDialog(xrcModuleManagerDialog):
	def __init__(self, parent):
		super(ModuleManagerDialog, self).__init__(parent)
		self.gui_delete.Bind(wx.EVT_BUTTON, self.on_delete)
		self.gui_unlock.Bind(wx.EVT_BUTTON, self.on_unlock)
		self.tree = PathModuleTree(self.filterable_tree_holder)
		self.filterable_tree_holder.Sizer.Add(self.tree, 1, wx.GROW)
		self.filterable_tree_holder.Layout()
		self.Size = 500, 400
		self.Bind(wx.EVT_WINDOW_DESTROY, lambda evt:
			(evt.Skip(), biblemgr.on_after_reload.remove(self.recreate)))
		
		biblemgr.on_after_reload += self.recreate
	
	def recreate(self, biblemgr):
		self.tree.recreate()		
	
	def on_delete(self, event):
		checked_modules = self.get_checked()
		if not checked_modules:
			wx.MessageBox(_("Please select some books to delete"), 
				_("Select books"))
			return
		
		if wx.YES == wx.MessageBox(_(
"""You are about to delete books.
This will completely remove the books and free up the disk space that they used.
You cannot undo this operation. Are you sure you want to delete these books?"
Books to be deleted:""") + '\n' + 
	', '.join([item.GetData().data.Name() for item in checked_modules]),
		_("Confirm book deletion"),
		wx.YES_NO, parent=self):
			items = [
				item.GetData().data.Name() for item in checked_modules
			]
			try:
				for item in checked_modules:
					module = item.GetData().data
					mgr = item.GetParent().GetData().data
					for book in (biblemgr.bible, biblemgr.commentary,
								 biblemgr.genbook, biblemgr.dictionary):
						#if str(module) == str(book.mod):
						#	import code
						#	code.InteractiveConsole(locals()).interact()
						### TODO: work out who's still got TK's hanging around
						if module in book.GetModules():
							book.cleanup_module(module)
							if book.mod == module:
								good_books = [
									x for x in book.GetModuleList() 
									if x not in items
								]
								if good_books:
									book_to_set = good_books[0]
								else:
									book_to_set = None

								
								## if we don't set a book here,
								## genbooktree.getpreviousitem won't be called
								## in SetReference, and data still hangs 
								## around... So deleting the last book might
								## not be possible at the moment
								book.SetModule(
									book_to_set,
									#None,
									#"Josephus", 
								notify=True)
#							wx.SafeYield()	

							break
					#else:
					#	dprint(ERROR, 
					#		"Couldn't clean up module as book not found for it", 
					#		module.Name())

					InstallMgr.removeModule(mgr, module.Name())
			finally:
				biblemgr.reload()
				self.tree.recreate()
	
	def on_unlock(self, event):
		selection = self.tree.tree.GetSelection()
		if not selection or not isinstance(selection.GetData().data, SW.Module):
			wx.MessageBox(_("Please select a book to unlock"), 
				_("Select a book"))
			return
		
		mod = selection.GetData().data
		
		for name, b in self.tree.module_types:
			if mod.Type() == b.type:
				if b.get_cipher_code(mod) is None:
					wx.MessageBox(
						_("This book is not locked at all, and doesn't "
						"need to be unlocked"), _("Not locked")
					)
					return
					
				d = wx.TextEntryDialog(self, 
					_("Unlock code for %s") % mod.Name(),
					_("Unlock code"),
					b.get_cipher_code(mod)
				)
				
				try:

					if d.ShowModal() == wx.ID_OK:
						b.unlock(mod, str(d.GetValue()))
				except book.FileSaveException, e:
					wx.MessageBox(e, _("Error"))
				except EnvironmentError, e:
					wx.MessageBox(
						_("Couldn't find config file. Error given was:")+
						str(e), _("Error")
					)

				finally:
					d.Destroy()
	
	def get_checked(self):
		tree = self.tree.tree
		root = tree.GetRootItem()
		assert root

		checked_items = []
		def iterate(item):
			if item.IsChecked():
				yield item
			
			child, cookie = tree.GetFirstChild(item)
		
			while child:
				for c in iterate(child):
					yield c

				child, cookie = tree.GetNextChild(item, cookie)
		
		checked_modules = [x for x in iterate(root)
			if isinstance(x.GetData().data, SW.Module)]

		if not checked_modules:
			selection = self.tree.tree.GetSelection()
			if selection and isinstance(selection.GetData().data, SW.Module):
				checked_modules = selection,

		return checked_modules

if __name__ == '__main__':
	import util.i18n
	util.i18n.initialize()
	app = wx.App(0)
	ModuleManagerDialog(None).ShowModal()
