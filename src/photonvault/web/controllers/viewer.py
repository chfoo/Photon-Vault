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
			URLSpec('/full/(.+)', FullViewHandler)
		]
	
	def init(self):
		self.application.controllers[Database].db[
			Item.COLLECTION].ensure_index(Item.DATE)
		self.application.controllers[Database].db[
			Item.COLLECTION].ensure_index(Item.TAGS)
		

class ViewMixIn(object):
	SORT_BY_DATE = 'date'
	SORT_BY_DATE_UPLOADED = 'date_uploaded'
	
	def get_items_newer(self, date, limit=100, sort_by=SORT_BY_DATE, tag=None):
		return self._get_items(date, False, limit, sort_by, tag)
	
	def get_items_older(self, date, limit=100, sort_by=SORT_BY_DATE, tag=None):
		return self._get_items(date, True, limit, sort_by, tag)
	
	def _get_items(self, date, older=False, limit=100, sort_by=SORT_BY_DATE, tag=None):
		if sort_by == ViewMixIn.SORT_BY_DATE_UPLOADED:
			sort_key = '_id'
		else:
			sort_key = Item.DATE
		
		if not older:
			criteria = {sort_key: {'$gt': date}}
		else:
			criteria = {sort_key: {'$lt': date}}
		
		if tag:
			criteria[Item.TAGS] = tag
		
		results = self.controllers[Database].db[Item.COLLECTION].find(
			criteria,
			limit=limit,
			sort=[(sort_key, 
				pymongo.ASCENDING if not older else pymongo.DESCENDING)],
		)
		
		if not older:
			return results
		else:
			return reversed(list(results))
	
	def get_item_count(self):
		return self.controllers[Database].db[Item.COLLECTION].count()


class OverviewHandler(RequestHandler, ViewMixIn):
	@render_response
	def get(self, tag=None):
		limit = 100
		count = self.get_item_count()
		newer_date_str = self.get_argument('newer_date', None)
		older_date_str = self.get_argument('older_date', None)
		
		if newer_date_str:
			newer_date = iso8601.parse_date(newer_date_str)
		else:
			newer_date = None
			
		if older_date_str:
			older_date = iso8601.parse_date(older_date_str)
		else:
			older_date = None
		
		if not newer_date and not older_date:
			older_date = datetime.datetime.utcnow()
	
		if newer_date:
			date = newer_date
			items = list(self.get_items_newer(date, limit + 1, tag=tag))
			items = list(reversed(items))
			has_newer = len(items) > limit
			
			if items:
				items_opposite_dir = list(self.get_items_older(
					items[-1][Item.DATE], 1, tag=tag))
				has_older = len(items_opposite_dir) != 0
			else:
				has_older = False
		else:
			date = older_date
			items = list(self.get_items_older(date, limit + 1, tag=tag))
			items = list(reversed(items))
			has_older = len(items) > limit
			
			if items:
				items_opposite_dir = list(self.get_items_newer(
					items[0][Item.DATE], 1, tag=tag))
				has_newer = len(items_opposite_dir) != 0
			else:
				has_newer = False
		
		return {
			'_template': 'viewer/overview.html',
			'items': items[:limit],
			'tag': tag,
			'paging': {
				'date': str(date),
				'limit': limit,
				'count': count,
				'has_older': has_older,
				'has_newer': has_newer,
			},
		}


class SingleViewHandler(RequestHandler, ViewMixIn):
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
			
			newer_result = list(self.get_items_newer(result[Item.DATE], 1))
			
			if newer_result:
				d['newer'] = str(newer_result[0]['_id'])
			
			older_result = list(self.get_items_older(result[Item.DATE], 1))
			
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
		