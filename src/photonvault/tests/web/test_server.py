#encoding=utf8
'''Test server'''
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
from photonvault.web.app import Application
from tornado.testing import AsyncHTTPTestCase
import httplib
import os.path
import unittest


class ServerBase(AsyncHTTPTestCase):
	def get_app(self):
		config_path = os.path.join(os.path.dirname(__file__),
			'test_config.conf')
		
		return Application(config_path)


class TestServer(ServerBase):
	def test_basic(self):
		'''It should return OK on /''' 
		response = self.fetch('/')
		self.assertEqual(response.code, httplib.OK)
	
	def test_script_resource(self):
		'''It should return javascript file'''
		response = self.fetch('/resource/scripts.js')
		self.assertEqual(response.code, httplib.OK)
		self.assertEqual(response.headers['Content-Type'], 'application/javascript')
		
	def test_style_resource(self):
		'''It should return stylesheet file'''
		response = self.fetch('/resource/styles.css')
		self.assertEqual(response.code, httplib.OK)
		self.assertEqual(response.headers['Content-Type'], 'text/css')

if __name__ == "__main__":
	#import sys;sys.argv = ['', 'Test.testName']
	unittest.main()