#encoding=utf8
'''Thumbnail generation'''
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
from photonvault.web.controllers.base.handler import BaseHandler
from photonvault.web.controllers.database import Database
from photonvault.web.models.collection import Item, Thumbnail
from tornado.web import Controller, URLSpec, StreamingFileMixIn, HTTPError
import PIL.Image
import bson
import bson.binary
import cStringIO
import datetime
import httplib
import photonvault.utils.exif
import shutil
import tempfile

__docformat__ = 'restructuredtext en'


class ThumbnailGenerator(Controller):
	def get_handlers(self):
		return [
			URLSpec('/thumbnail/([0-9a-fA-F]+)/([0-9]+)', ThumbnailHandler),
		]
	

class ThumbnailHandler(BaseHandler, StreamingFileMixIn):
	SIZES = [50, 200, 500]
	ORIENTATION_MAP = {
		8: PIL.Image.ROTATE_90,
		3: PIL.Image.ROTATE_180,
		6: PIL.Image.ROTATE_270,
	}
	
	def head(self, item_id_str, size):
		self.get(item_id_str, size)
	
	def get(self, item_id_str, size):
		if int(size) not in ThumbnailHandler.SIZES:
			raise HTTPError(httplib.NOT_FOUND)
		
		item_id = bson.objectid.ObjectId(item_id_str)
		
		result = self.get_thumbnail(item_id, size)
		
		if not result:
			self.new_thumbnail(item_id, int(size))
			result = self.get_thumbnail(item_id, size)
		
		last_modified = result[Thumbnail.Size.TIME]
		data = cStringIO.StringIO(result[Thumbnail.Size.DATA])
		
		self.serve_file(data, size=len(result[Thumbnail.Size.DATA]), 
			last_modified=last_modified, mimetype="image")
	
	def get_file(self, item_id):
		result = self.controllers[Database].db[Item.COLLECTION].find_one(
			{'_id': item_id})
		
		if result:
			file_id = result[Item.FILE_ID]
			file_obj = self.controllers[Database].fs.get(file_id)
			
			return file_obj
	
	def new_thumbnail(self, item_id, size):
		file_obj = self.get_file(item_id)
		
		with tempfile.SpooledTemporaryFile(max_size=4194304) as new_file:
			image = PIL.Image.open(file_obj)
			new_image = self.apply_orientation(image)
			
			new_image.thumbnail([size, size], PIL.Image.ANTIALIAS)
			new_image.save(new_file, image.format)
			new_file.seek(0)
			
			self.controllers[Database].db[Thumbnail.COLLECTION].update(
				{'_id': item_id},
				{'$set': {
					'%s.%s' % (Thumbnail.SIZES, size) : {
						Thumbnail.Size.TIME: datetime.datetime.utcnow(),
						Thumbnail.Size.DATA: bson.binary.Binary(new_file.read()),
					}
				}
			}, upsert=True)
		
	def get_thumbnail(self, item_id, size):
		result = self.controllers[Database].db[Thumbnail.COLLECTION].find_one(
			{'_id': item_id, '%s.%s' % (Thumbnail.SIZES, size) : {'$exists': True}}
		)
		
		if result:
			return result[Thumbnail.SIZES][size]
	
	def apply_orientation(self, pil_image):
		# Quick hack for exif info
		# http://stackoverflow.com/questions/765396/
		
		orientation_value = photonvault.utils.exif.get_orientation_quick(pil_image)
		
		if orientation_value in ThumbnailHandler.ORIENTATION_MAP:
			pil_image = pil_image.transpose(
				ThumbnailHandler.ORIENTATION_MAP[orientation_value])
		
		return pil_image