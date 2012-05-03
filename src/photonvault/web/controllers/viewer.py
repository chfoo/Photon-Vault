#encoding=utf8
'''Web views'''
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
from photonvault.web.models.collection import Item
from photonvault.web.utils.render import render_response
from tornado.web import Controller, RequestHandler, URLSpec, HTTPError, \
	StreamingFileMixIn
import bson.objectid
import httplib
import pymongo

__docformat__ = 'restructuredtext en'


class Viewer(Controller):
	def get_handlers(self):
		return [
			URLSpec('/', OverviewHandler),
			URLSpec('/item/(.+)', SingleViewHandler),
			URLSpec('/full/(.+)', FullViewHandler)
		]


class ViewMixIn(object):
	SORT_DATE = 'date'
	SORT_DATE_UPLOADED = 'date_uploaded'
	ORDER_ASCENDING = 'ascending'
	ORDER_DESCENDING = 'descending'
	
	def get_items(self, page=0, limit=100, sort=SORT_DATE_UPLOADED, 
	order=ORDER_DESCENDING):
		if sort == ViewMixIn.SORT_DATE_UPLOADED:
			sort_key = '_id'
		else:
			sort_key = Item.DATE
		
		if order == ViewMixIn.ORDER_ASCENDING:
			sort_direction = pymongo.ASCENDING
		else:
			sort_direction = pymongo.DESCENDING
	
		return self.controllers[Database].db[Item.COLLECTION].find(
			skip=page * limit,
			limit=limit,
			sort=[(sort_key, sort_direction)],
		)
	
	def get_item_count(self):
		return self.controllers[Database].db[Item.COLLECTION].count()


class OverviewHandler(RequestHandler, ViewMixIn):
	@render_response
	def get(self):
		limit = 100
		count = self.get_item_count()
		page = max(0, int(self.get_argument('page', 0)))
		items = list(self.get_items(page, limit=100, sort=ViewMixIn.SORT_DATE))
		
		return {
			'_template': 'viewer/overview.html',
			'items': items,
			'paging': {
				'page': page,
				'limit': limit,
				'count': count,
			},
		}


class SingleViewHandler(RequestHandler, ViewMixIn):
	@render_response
	def get(self, str_id):
		obj_id = bson.objectid.ObjectId(str_id)
		
		result = self.controllers[Database].db[Item.COLLECTION].find_one(
			{'_id': obj_id})
		
		if result:
			return {
				'_template': 'viewer/single.html',
				'item': result,
			}
		else:
			raise HTTPError(httplib.NOT_FOUND)


class FullViewHandler(RequestHandler, StreamingFileMixIn):
	def head(self, str_id):
		self.get(str_id)
	
	def get(self, str_id):
		obj_id = bson.objectid.ObjectId(str_id)
		
		result = self.controllers[Database].db[Item.COLLECTION].find_one(
			{'_id': obj_id})
		
		if result:
			f = self.controllers[Database].fs.get(result[Item.FILE_ID])
			
			if f:
				self.serve_file(f, download_filename=result[Item.TITLE], 
					mimetype='image', size=f.length, 
					last_modified=f.upload_date)
				return
		
		raise HTTPError(httplib.NOT_FOUND)
		