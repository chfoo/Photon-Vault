#encoding=utf8
'''Base handler'''
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
from tornado.web import RequestHandler
import httplib
import traceback

__docformat__ = 'restructuredtext en'


class BaseHandler(RequestHandler):
	def write_error(self, status_code, **kwargs):
		self.set_status(status_code)
		self.set_header('Content-Type', 'text/plain')
		self.write('Error %s %s\n' % (status_code, httplib.responses.get(status_code)))
		
		if 'exc_info' in kwargs:
			for line in traceback.format_exception(*kwargs['exc_info']):
				self.write(line.encode('utf8'))
		
		self.finish()