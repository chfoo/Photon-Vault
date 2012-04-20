#encoding=utf8
'''Test photo processing'''
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
from photonvault.tests.web.test_server import ServerBase
import httplib
import os.path
import unittest
import urllib3.filepost

class TestProcessor(ServerBase):
	@property
	def data_dir(self):
		return os.path.join(os.path.dirname(__file__), 'data')
	
	def test_upload(self):
		'''It should accept a single image''' 
		
		file_data = open(os.path.join(self.data_dir, 'image.png'), 'rb').read()
		
		post_data, content_type = urllib3.filepost.encode_multipart_formdata([
			('file', file_data)])
		response = self.fetch('/upload', 
			method='POST',
			headers={'Content-Type': content_type},
			body=post_data,
		)
		self.assertEqual(response.code, httplib.OK)
	

if __name__ == "__main__":
	#import sys;sys.argv = ['', 'Test.testName']
	unittest.main()