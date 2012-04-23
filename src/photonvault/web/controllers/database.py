#encoding=utf8
'''MongoDB database controller'''
#
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
#
from tornado.web import RequestHandler, URLSpec
import gridfs
import pymongo.connection
import tornado.web

__docformat__ = 'restructuredtext en'

class Database(tornado.web.Controller):
	def get_handlers(self):
		
		if self.application.config_parser.has_option(u'database', 
		u'debug-allow-drop-all') and self.application.config_parser.getboolean(
		u'database', u'debug-allow-drop-all'):
			return [URLSpec('/database/drop', DropHandler)]
		
		return []
	
	def init(self):
		host = u'localhost'
		port = 27017
		
		if self.application.config_parser.has_option(u'database', u'host'):
			host = self.application.config_parser.get(u'database', u'host')
			
		if self.application.config_parser.has_option(u'database', u'port'):
			port = self.application.config_parser.getint(u'database', u'port')
		
		self.connection = pymongo.connection.Connection(host, port)
	
	@property
	def db(self):
		name = u'photonvault'
		
		if self.application.config_parser.has_option(u'database', u'name'):
			name = self.application.config_parser.get(u'database', u'name')
		
		return self.connection[name]
	
	@property
	def fs(self):
		return gridfs.GridFS(self.db)


class DropHandler(RequestHandler):
	def get(self):
		db = self.controllers[Database].db
		
		for name in db.collection_names():
			if not name.startswith(u'system'):
				db.drop_collection(name)
			
		self.finish()