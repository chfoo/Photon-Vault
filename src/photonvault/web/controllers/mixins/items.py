#encoding=utf8
'''Get items'''
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
import pymongo
import bson.objectid

__docformat__ = 'restructuredtext en'


class ItemPaginationMixin(object):
	def get_paginated_items(self, limit=100, tag=None, reverse_chron=False):
		newer_obj_id, older_obj_id = self.get_item_request_arguments()
		
		d = {
			'items': [],
			'has_more_newer': False,
			'has_more_older': False,
		}
		
		both_empty = not newer_obj_id and not older_obj_id 
		
		if newer_obj_id or both_empty and not reverse_chron:
			items = list(self.get_items_newer(newer_obj_id, limit + 1, tag))
			if reverse_chron:
				items = list(reversed(items))
			d['items'] = items[:limit]
			d['has_more_newer'] = len(items) > limit
			d['has_more_older'] = self.has_older_than(newer_obj_id, tag)
		elif older_obj_id or both_empty and reverse_chron:
			items = list(self.get_items_older(older_obj_id, limit + 1, tag))
			if reverse_chron:
				items = list(reversed(items))
			d['items'] = items[:limit]
			d['has_more_older'] = len(items) > limit
			d['has_more_newer'] = self.has_newer_than(older_obj_id, tag)
		
		return d
	
	def get_item_request_arguments(self):
		newer_str = self.get_argument('newer_than', None)
		older_str = self.get_argument('older_than', None)
		newer_obj_id = None
		older_obj_id = None
		
		if newer_str:
			newer_obj_id = bson.objectid.ObjectId(newer_str)
			
		if older_str:
			older_obj_id = bson.objectid.ObjectId(older_str)
		
		return (newer_obj_id, older_obj_id)
	
	def has_older_than(self, item_id, tag=None, by_creation_date=True):
		if item_id:
			return len(self.get_items_older(item_id, 1, tag, 
				by_creation_date)) > 0
	
	def has_newer_than(self, item_id, tag=None, by_creation_date=True):
		if item_id:
			return len(self.get_items_newer(item_id, 1, tag, 
				by_creation_date)) > 0
	
	def get_items_newer(self, item_id, limit=100, tag=None, 
	by_creation_date=True):
		return self._get_items(item_id, False, limit, tag, by_creation_date)
	
	def get_items_older(self, item_id, limit=100, tag=None,
	by_creation_date=True):
		return self._get_items(item_id, True, limit, tag, by_creation_date)
	
	def _get_items(self, item_id, older=False, limit=100, tag=None,
	by_creation_date=True):
		criteria = {}
		
		if item_id:
			item = self.controllers[Database].db[Item.COLLECTION].find_one(
				{'_id': item_id})
		
			if not item:
				raise Exception('Item not found=%s' % item_id)
		
			if not older:
				key = '$gt'
			else:
				key = '$lt'
			
			if by_creation_date:
				criteria['$or'] = [
					{
						Item.DATE: {key: item[Item.DATE]}
					},
					{
						Item.DATE: item[Item.DATE],
						'_id': {key: item['_id']}
					},
				]
			else:
				criteria['_id'] = {key: item['_id']}
					
		if tag:
			criteria[Item.TAGS] = tag
		
		direction = pymongo.ASCENDING if not older else pymongo.DESCENDING
		sort_keys = [('_id', direction)]
		
		if by_creation_date:
			sort_keys.insert(0, (Item.DATE, direction))
		
		results = self.controllers[Database].db[Item.COLLECTION].find(
			criteria,
			limit=limit,
			sort=sort_keys,
		)
		
		if not older:
			return list(results)
		else:
			return list(reversed(list(results)))
	
	def get_item_count(self):
		return self.controllers[Database].db[Item.COLLECTION].count()
	
	def get_earliest_year(self):
		result = self.controllers[Database].db[Item.COLLECTION].find_one(
			sort=[(Item.DATE, pymongo.ASCENDING), ('_id', pymongo.ASCENDING)],
			fields=[Item.DATE],
		)
		
		if result:
			return result[Item.DATE].year
