#encoding=utf8
'''Stylesheet and scripts resource optimizer'''

# This file is part of Photon Vault.
# 
# Photon Vault is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Photon Vault is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Photon Vault.  If not, see <http://www.gnu.org/licenses/>.

__docformat__ = 'restructuredtext en'

from tornado.web import Controller, URLSpec, StaticFileHandler
import glob
import os.path
import shutil
import tempfile
import photonvault.web.views


class Resource(Controller):
	def get_handlers(self):
		return [
			URLSpec('/resource/scripts.js', ScriptsHandler),
			URLSpec('/resource/styles.css', StylesHandler),
		]
	
	def init(self):
		self.build_resources()
	
	def build_resources(self):
		self.scripts_file = tempfile.NamedTemporaryFile('wt', suffix='.js')
		self.styles_file = tempfile.NamedTemporaryFile('wt', suffix='.css')
		self.scripts_file_dir, self.scripts_file_name = os.path.split(
			self.scripts_file.name)
		self.styles_file_dir, self.styles_file_name = os.path.split(
			self.styles_file.name)
		self.concatinate_scripts(self.scripts_file)
		self.concatinate_styles(self.styles_file)
	
	def concatinate_scripts(self, destination_file):
		self.concatinate_something(destination_file, u'scripts', u'js')
	
	def concatinate_styles(self, destination_file):
		self.concatinate_something(destination_file, u'styles', u'css')
	
	def concatinate_something(self, destination_file, source_type, 
	file_extension):
		resource_path = os.path.join(os.path.dirname(
			photonvault.web.views.__file__), 'resource')
		source_dir = os.path.join(resource_path, source_type)
		filenames = glob.glob(u'%s/*.%s' % (source_dir, file_extension)) + \
			glob.glob(u'%s/*/*.%s' % (source_dir, file_extension))
		
		# Open as text so byte order marks are not accidentally included 
		for filename in filenames:
			with open(filename, 'rt') as f_in:
				shutil.copyfileobj(f_in, destination_file)
			
			destination_file.write('\n')
		
		destination_file.flush()
	
	def __del__(self):
		del self.scripts_file
		del self.styles_file
		
		Controller.__del__(self)

class ScriptsHandler(StaticFileHandler):
	def initialize(self):
		StaticFileHandler.initialize(self, 
			self.controllers[Resource].scripts_file_dir)
	
	def get(self):
		StaticFileHandler.get(self, 
			self.controllers[Resource].scripts_file_name)
	
	def head(self):
		StaticFileHandler.head(self, 
			self.controllers[Resource].scripts_file_name)


class StylesHandler(StaticFileHandler):
	def initialize(self):
		StaticFileHandler.initialize(self, 
			self.controllers[Resource].styles_file_dir)
	
	def get(self):
		StaticFileHandler.get(self, 
			self.controllers[Resource].styles_file_name)
	
	def head(self):
		StaticFileHandler.head(self, 
			self.controllers[Resource].styles_file_name)
	
	