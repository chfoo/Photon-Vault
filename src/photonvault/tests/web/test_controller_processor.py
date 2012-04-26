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
from photonvault.tests.web.test_server import ServerBase, DatabaseCleanUpMixIn
import httplib
import json
import os.path
import time
import unittest
import urllib3.filepost


class UploadMixIn(object):
	@property
	def data_dir(self):
		return os.path.join(os.path.dirname(__file__), 'data')
	
	def _upload(self, filename, use_json=True):
		file_data = open(os.path.join(self.data_dir, filename), 'rb').read()
		
		post_data, content_type = urllib3.filepost.encode_multipart_formdata([
			('file', file_data)])
		response = self.fetch('/upload?_format=json' if use_json else '/upload', 
			method='POST',
			headers={'Content-Type': content_type},
			body=post_data,
		)
		
		self.assertEqual(response.code, httplib.OK)
		
		if use_json:
			json_response = json.loads(response.body)
			
			self.assertNotEqual(json_response['bytes_read'], 0)
			self.assertEqual(json_response['bytes_read'], len(file_data))
		else:
			self.assertNotEqual(len(response.body), 0)
	

class TestProcessor(ServerBase, UploadMixIn, DatabaseCleanUpMixIn):
	def test_upload_image(self):
		'''It should accept a single image''' 
		
		self._upload('image.png')
		self._upload('image.png', False)
	
	def test_upload_tgz(self):
		'''It should accept a tar.gz file''' 
		
		self._upload('image.png.tar.gz')
		self._upload('image.png.tar.gz', False)
		
	def test_upload_zip(self):
		'''It should accept a zip file''' 
		
		self._upload('image.png.zip')
		self._upload('image.png.zip', False)
	
	def test_process_queue(self): 
		'''It should process the queue until empty and images should be saved'''
		
		self._upload('image.png')
		self._upload('tagged_image.png')
		
		for i in range(1, 10):
			response = self.fetch('/upload_queue?_format=json')
			
			self.assertEqual(response.code, httplib.OK)
			
			json_response = json.loads(response.body)
		
			if len(json_response['files']) == 0:
				break
			
			time.sleep(0.5)
		
			if i == 10:
				raise Exception('Failed to process queue')

if __name__ == "__main__":
	#import sys;sys.argv = ['', 'Test.testName']
	unittest.main()