#encoding=utf8
'''Application instance'''

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


from photonvault.web.controllers.database import Database
from photonvault.web.controllers.edit import Edit
from photonvault.web.controllers.processor import Processor
from photonvault.web.controllers.resource import Resource
from photonvault.web.controllers.thumbnail import ThumbnailGenerator
from photonvault.web.controllers.viewer import Viewer
import ConfigParser
import os.path
import photonvault.web
import tornado.web

class Application(tornado.web.Application):
	def __init__(self, config_filename):
		self.config_parser = ConfigParser.SafeConfigParser()
		self.config_parser.read([config_filename])
		
		tornado.web.Application.__init__(self, 
			controllers=[
				Database,
				Resource,
				Viewer,
				Processor,
				ThumbnailGenerator,
				Edit,
			],
			template_path=self._get_template_path(),
		)
	
	def _get_template_path(self):
		return os.path.join(os.path.dirname(photonvault.web.views.__file__),
			'templates')
	
	