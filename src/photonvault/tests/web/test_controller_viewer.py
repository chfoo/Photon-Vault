#encoding=utf8
'''Test photo viewing'''
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
from photonvault.tests.web.test_controller_processor import UploadMixIn
from photonvault.tests.web.test_server import ServerBase, DatabaseCleanUpMixIn
import httplib
import json
import unittest


class TestViewer(ServerBase, UploadMixIn, DatabaseCleanUpMixIn):
	def test_overview(self):
		'''It should render page with two thumbnails'''
		
		self._upload('image.png')
		self._upload('tagged_image.png')
		
		response = self.fetch('/')
		
		self.assertEqual(response.code, httplib.OK)
		
		response = self.fetch('/?_format=json')
		
		self.assertEqual(response.code, httplib.OK)
		
		json_response = json.loads(response.body)
		
		self.assertEqual(len(json_response['items']), 2)
		
	
if __name__ == "__main__":
	#import sys;sys.argv = ['', 'Test.testName']
	unittest.main()