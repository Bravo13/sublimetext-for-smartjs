import sublime, sublime_plugin, smartjs_api, os, re

device = smartjs_api.new()

def getName(item):
	return item['name']

def fix_windows_path(file):
	if os.name == 'nt':
		file = file.replace('\\', '/')
		file = re.sub('^([A-Za-z]):', '/\\1', file)
		file = file[0:2].upper() + file[2:]
	return file
	
class SmartjsManagerCommand(sublime_plugin.WindowCommand):
	def run(self):
		sublime.active_window().show_quick_panel(map(getName, device.list_ports()), self.openConnection)

	def openConnection(self, portId):
		if portId == -1:
			return
		ports = device.list_ports()
		device.serial_params['port'] = ports[portId]['name']
		device.connect()
		self.showFilesList()

	def showFilesList(self):
		return sublime.active_window().show_quick_panel(['Disconnect', 'New file'] + map(getName, device.list_files()), self.showFilesListAction)

	def showFilesListAction(self, item):
		print item
		if item == 0:
			device.close()
		elif item == 1:
			self.showNewFile()
		else:
			files = device.list_files()
			self.openFile(files[item-2])

	def showNewFile(self):
		return sublime.active_window().show_input_panel('Create file', 'newFile.js', self.showNewFileAction, '', self.showFilesList)

	def showNewFileAction(self, fileName):
		file = { 'name': fileName}
		device.createFile(file)
		return self.showFilesList()

	def openFile(self, file):
		local_path = os.path.join(sublime.packages_path(), 'User', 'Smartjs', file['name'])
		device.downloadFile(file, local_path)
		self.window.run_command('open_file', {'file': fix_windows_path(local_path)})
		print local_path
		view = self.window.active_view()
		view.settings().set('local_path', local_path)
		view.settings().set('smartjs_file', file)
		view.settings().set('remote', 1)
		view.settings().set('port', device.serial_params['port'])
		view.settings().set('baudrate', device.serial_params['baudrate'])
		print file

class SmartjsListener(sublime_plugin.EventListener):

	def on_post_save(self, view):
		settings = view.settings();
		_dev = smartjs_api.new()
		_dev.serial_params['port'] = settings.get('port')
		_dev.serial_params['baudrate'] = settings.get('baudrate')
		if settings.get('remote'):
			_dev.uploadFile(settings.get('smartjs_file'), settings.get('local_path'))
		return 1
		