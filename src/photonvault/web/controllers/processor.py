#encoding=utf8
'''Photo and video processing'''
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

__docformat__ = 'restructuredtext en'

from photonvault.web.controllers.database import Database
from photonvault.web.models.collection import UploadQueue
from photonvault.web.utils.render import render_response
from tornado.web import Controller, RequestHandler, URLSpec, FileUploadHandler
import shutil


class Processor(Controller):
	def get_handlers(self):
		return [
			URLSpec('/upload', UploadHandler),
		]


class QueueViewHandler(RequestHandler):
	def get(self):
		pass

class UploadHandler(FileUploadHandler):
	def get(self):
		self.render('processor/upload.html')
	
	def post(self):
		self.start_reading()
	
	@render_response
	def upload_finished(self):
		dest_f = self.controllers[Database].fs.new_file(
			filename=self.field_storage['file'].filename)
		
		shutil.copyfileobj(self.field_storage['file'].file, dest_f)
		dest_f.close()
		
		file_id = dest_f._id
		
		upload_queue = self.controllers[Database].db[UploadQueue.COLLECTION]
		upload_queue.insert({
			UploadQueue.FILE_ID: file_id
		})
		
		bytes_read = self.field_storage['file'].file.tell()
		
		return {
			'_template': 'processor/upload.html',
			'bytes_read': bytes_read,
			'file_id': str(file_id),
			'_redirect': '/queue',
		}
