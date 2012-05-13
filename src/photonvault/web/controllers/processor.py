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
import pymongo
import gridfs

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
		
		host, port = Database.get_host_and_port(self.application.config_parser)
		dbname = Database.get_database_name(self.application.config_parser)
		self.queue_processor = QueueProcessor(self.queue_processor_event, 
			host, port, dbname)
		
		self.queue_processor.start()


class QueueProcessor(multiprocessing.Process):
	SLEEP_TIME = 43200 # 12 hours
	
	def __init__(self, queue_processor_event, host, port, database_name):
		multiprocessing.Process.__init__(self)
		self.daemon = True
		self.queue_processor_event = queue_processor_event
		self.host = host
		self.port = port
		self.database_name = database_name
	
	def run(self):
		# Connection deferred to here for Windows multiprocessing compatibility
		self.logger = logging.getLogger(__name__)
		
		# for Windows debugging:
		# logging.basicConfig(filename="photonvaultlog.txt", level=logging.DEBUG)
		
		self.connection = pymongo.connection.Connection(self.host, self.port)
		self.db = self.connection[self.database_name]
		self.fs = gridfs.GridFS(self.db)
		
		while True:
			self.logger.debug('Processor sleeping')
			
			self.queue_processor_event.wait(
				QueueProcessor.SLEEP_TIME)
			self.queue_processor_event.clear()
			
			self.logger.debug('Processor woken')
			
			# Database may not be finished committing, wait a bit
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
				temp_file = tempfile.NamedTemporaryFile(delete=False)
			
				shutil.copyfileobj(file_obj, temp_file)
				temp_file.close()
				
				if not self.attempt_read_tar_file(temp_file.name):
					if not self.attempt_read_zip_file(temp_file.name):
						self.insert_image(temp_file.name, original_filename)
				
				os.remove(temp_file.name)
				self.db[UploadQueue.COLLECTION].remove({'_id': result['_id']})
				self.fs.delete(result[UploadQueue.FILE_ID])
			
	
	def attempt_read_tar_file(self, path):
		self.logger.debug('Attempt to read tar file')
		
		try:
			tar_file = tarfile.TarFile(path, mode='r')
		except tarfile.ReadError:
			self.logger.debug('Could not read tar file')
			return
		
		for member in tar_file.getmembers():
			self.logger.debug('Got tar member %s', member.name)
			
			if member.isfile():
				f = tar_file.extractfile(member)
				dest_f = tempfile.NamedTemporaryFile(delete=False)
				
				shutil.copyfileobj(f, dest_f)
				dest_f.close()
				self.insert_image(dest_f.name, member.name)
				os.remove(dest_f.name)
		
		return True
		
	def attempt_read_zip_file(self, path):
		self.logger.debug('Attempt read zip file')
		
		try:
			zip_file = zipfile.ZipFile(path, mode='r')
		except zipfile.BadZipfile:
			self.logger.debug('Could not read zip file')
			return
		
		for info in zip_file.infolist():
			self.logger.debug('Got zip member %s', info.filename)
			f = zip_file.open(info.filename)
			
			dest_f = tempfile.NamedTemporaryFile(delete=False)
			
			shutil.copyfileobj(f, dest_f)
			dest_f.close()
			self.insert_image(dest_f.name, info.filename)
			os.remove(dest_f.name)
		
		return True
	
	def insert_image(self, path, filename):
		self.logger.debug('Attempt insert image with name %s', filename)

		if self.is_readable_image(path):
			db_file = self.fs.new_file(filename=filename)
			
			with open(path, 'rb') as file_obj:
				shutil.copyfileobj(file_obj, db_file)
			
			db_file.close()
			
			file_id = db_file._id
			
			date = self.extract_date(path) or datetime.datetime.utcnow()
			
			self.db[Item.COLLECTION].insert({
				Item.FILE_ID: file_id,
				Item.TITLE: filename,
				Item.DATE: date,
			})
			
			self.logger.debug('Inserted image, file id=%s', file_id)
			
			return True
	
	def is_readable_image(self, path):
		try:
			PIL.Image.open(path)
		except IOError:
			# self.logger.exception("try read 1")
			return False
		except ValueError:
			# self.logger.exception("try read 2")
			return False
		
		return True
	
	def extract_date(self, path):
		metadata = pyexiv2.ImageMetadata(path)
		metadata.read()
		
		# We need the date of the content of the photo, not the date
		# when that photo was digitized
		if 'Xmp.photoshop.DateCreated' in metadata.xmp_keys:
			tag = metadata['Xmp.photoshop.DateCreated']
			
			return tag.value
		
		if 'Exif.Photo.DateTimeOriginal' in metadata.exif_keys:
			tag = metadata['Exif.Photo.DateTimeOriginal']
			
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
