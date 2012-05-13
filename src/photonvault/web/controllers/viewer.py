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
from photonvault.web.controllers.mixins.items import ItemPaginationMixin
from photonvault.web.models.collection import Item
from photonvault.web.utils.render import render_response
from tornado.web import Controller, RequestHandler, URLSpec, HTTPError, \
	StreamingFileMixIn
import bson.objectid
import datetime
import httplib
import iso8601
import pymongo

__docformat__ = 'restructuredtext en'


class Viewer(Controller):
	def get_handlers(self):
		return [
			URLSpec('/', OverviewHandler),
			URLSpec('/tag/(.+)', OverviewHandler),
			URLSpec('/item/(.+)', SingleViewHandler),
			URLSpec('/full/(.+)', FullViewHandler),
			URLSpec('/all_tags', AllTagsHandler),
		]
	
	def init(self):
		self.application.controllers[Database].db[
			Item.COLLECTION].ensure_index(Item.DATE)
		self.application.controllers[Database].db[
			Item.COLLECTION].ensure_index(Item.TAGS)
		

class OverviewHandler(RequestHandler, ItemPaginationMixin):
	@render_response
	def get(self, tag=None):
		limit = 100
		count = self.get_item_count()
		results = self.get_paginated_items(limit, tag, reverse_chron=True)
		
		return {
			'_template': 'viewer/overview.html',
			'items': results['items'],
			'tag': tag,
			'paging': {
				'limit': limit,
				'count': count,
				'has_more_older': results['has_more_older'],
				'has_more_newer': results['has_more_newer'],
			},
		}


class SingleViewHandler(RequestHandler, ItemPaginationMixin):
	@render_response
	def get(self, str_id):
		obj_id = bson.objectid.ObjectId(str_id)
		
		result = self.controllers[Database].db[Item.COLLECTION].find_one(
			{'_id': obj_id})
		
		if result:
			d = {
				'_template': 'viewer/single.html',
				'item': result,
			}
			
			newer_result = list(self.get_items_newer(obj_id, 1))
			
			if newer_result:
				d['newer'] = str(newer_result[0]['_id'])
			
			older_result = list(self.get_items_older(obj_id, 1))
			
			if older_result:
				d['older'] = str(older_result[0]['_id'])
			
			return d
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


class AllTagsHandler(RequestHandler):
	@render_response
	def get(self):
		tags = self.controllers[Database].db[Item.COLLECTION].distinct(
			Item.TAGS)
		
		return {
			'_template': 'viewer/all_tags.html',
			'tags': tags,
		}

