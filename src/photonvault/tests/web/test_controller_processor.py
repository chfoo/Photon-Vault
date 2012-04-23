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
from photonvault.tests.web.test_server import ServerBase, post_drop_database
import httplib
import json
import os.path
import unittest
import urllib3.filepost

class TestProcessor(ServerBase):
	@property
	def data_dir(self):
		return os.path.join(os.path.dirname(__file__), 'data')
	
	@post_drop_database
	def test_upload_image(self):
		'''It should accept a single image''' 
		
		self._upload('image.png')
	
	@post_drop_database
	def test_upload_tgz(self):
		'''It should accept a tar.gz file''' 
		
		self._upload('image.png.tar.gz')
		
	@post_drop_database
	def test_upload_zip(self):
		'''It should accept a zip file''' 
		
		self._upload('image.png.zip')
	
	def _upload(self, filename):
		file_data = open(os.path.join(self.data_dir, filename), 'rb').read()
		
		post_data, content_type = urllib3.filepost.encode_multipart_formdata([
			('file', file_data)])
		response = self.fetch('/upload?_format=json', 
			method='POST',
			headers={'Content-Type': content_type},
			body=post_data,
		)
		
		self.assertEqual(response.code, httplib.OK)
		
		json_response = json.loads(response.body)
		
		self.assertNotEqual(json_response['bytes_read'], 0)
		self.assertEqual(json_response['bytes_read'], len(file_data))
	

if __name__ == "__main__":
	#import sys;sys.argv = ['', 'Test.testName']
	unittest.main()