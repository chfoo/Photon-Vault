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
#
from photonvault.web.controllers.database import Database
from photonvault.web.models.collection import UploadQueue, Item
from photonvault.web.utils.render import render_response
from tornado.web import Controller, RequestHandler, URLSpec, FileUploadHandler
import PIL.Image
import datetime
import logging
import multiprocessing
import os.path
import pyexiv2
import shutil
import tarfile
import tempfile
import time
import zipfile

__docformat__ = 'restructuredtext en'

_logger = logging.getLogger(__name__)

class Processor(Controller):
	def get_handlers(self):
		return [
			URLSpec('/upload', UploadHandler),
			URLSpec('/upload_queue', QueueViewHandler)
		]
	
	def init(self):
		_logger.debug('Starting processor process')
		self.queue_processor_event = multiprocessing.Event()
		self.queue_processor = QueueProcessor(self)
		self.queue_processor.start()


class QueueProcessor(multiprocessing.Process):
	SLEEP_TIME = 43200 # 12 hours
	
	def __init__(self, controller):
		multiprocessing.Process.__init__(self)
		self.daemon = True
		self.controller = controller
		self.db = self.controller.application.controllers[Database].db
		self.fs = self.controller.application.controllers[Database].fs
	
	def run(self):
		while True:
			_logger.debug('Processor sleeping')
			
			self.controller.queue_processor_event.wait(
				QueueProcessor.SLEEP_TIME)
			self.controller.queue_processor_event.clear()
			
			_logger.debug('Processor woken')
			
			time.sleep(2)
			
			while self.db[UploadQueue.COLLECTION].count():
				# TODO: This logic assumes only 1 processor. Make this support
				# many processors
				result = self.db[UploadQueue.COLLECTION].find_one()
				
				if not result:
					continue
				
				file_id = result[UploadQueue.FILE_ID]
				file_obj = self.fs.get(file_id)
				original_filename = file_obj.filename
				temp_file = tempfile.NamedTemporaryFile()
			
				shutil.copyfileobj(file_obj, temp_file)
				temp_file.seek(0)
				
				if not self.attempt_read_tar_file(temp_file):
					if not self.attempt_read_zip_file(temp_file):
						self.insert_image(temp_file, original_filename)
				
				self.db[UploadQueue.COLLECTION].remove({'_id': result['_id']})
			
	
	def attempt_read_tar_file(self, file_obj):
		_logger.debug('Attempt to read tar file')
		
		try:
			tar_file = tarfile.TarFile(fileobj=file_obj, mode='r')
		except tarfile.ReadError:
			_logger.debug('Could not read tar file')
			file_obj.seek(0)
			return
		
		for member in tar_file.getmembers():
			_logger.debug('Got tar member %s', member.name)
			
			if member.isfile():
				f = tar_file.extractfile(member)
				
				self.insert_image(f, member.name)
		
		return True
		
	def attempt_read_zip_file(self, file_obj):
		_logger.debug('Attempt read zip file')
		
		try:
			zip_file = zipfile.ZipFile(file_obj, mode='r')
		except zipfile.BadZipfile:
			_logger.debug('Could not read zip file')
			file_obj.seek(0)
			return
		
		for info in zip_file.infolist():
			_logger.debug('Got zip member %s', info.filename)
			f = zip_file.open(info.filename)
			
			with tempfile.NamedTemporaryFile() as dest_f:
				shutil.copyfileobj(f, dest_f)
				dest_f.seek(0)
				self.insert_image(dest_f, info.filename)
		
		return True
	
	def insert_image(self, file_obj, filename):
		_logger.debug('Attempt insert image with name %s', filename)
		
		file_obj.seek(0)
		
		if self.is_readable_image(file_obj.name):
			db_file = self.fs.new_file(filename=filename)
			
			shutil.copyfileobj(file_obj, db_file)
			
			db_file.close()
			
			file_id = db_file._id
			
			file_obj.seek(0)
			
			date = self.extract_date(file_obj.name) or datetime.datetime.utcnow()
			
			self.db[Item.COLLECTION].insert({
				Item.FILE_ID: file_id,
				Item.TITLE: filename,
				Item.DATE: date,
			})
			
			_logger.debug('Inserted image, file id=%s', file_id)
			
			return True
	
	def is_readable_image(self, path):
		try:
			PIL.Image.open(path)
		except IOError:
			return False
		except ValueError:
			return False
		
		return True
	
	def extract_date(self, path):
		metadata = pyexiv2.ImageMetadata(path)
		metadata.read()
		
		if 'Exif.Image.DateTime' in metadata: 
			tag = metadata['Exif.Image.DateTime']
			
			return tag.value


class QueueViewHandler(RequestHandler):
	@render_response
	def get(self):
		l = []
		
		for result in self.controllers[Database].db[UploadQueue.COLLECTION].find():
			l.append({
				'file_id': str(result[UploadQueue.FILE_ID])
			})
		
		return {
			'files': l
		}


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
			UploadQueue.FILE_ID: file_id,
		})
		
		bytes_read = self.field_storage['file'].file.tell()
		
		self.controllers[Processor].queue_processor_event.set()
		
		return {
			'_template': 'processor/upload_success.html',
			'bytes_read': bytes_read,
			'file_id': str(file_id),
			'_redirect': '/queue',
		}
