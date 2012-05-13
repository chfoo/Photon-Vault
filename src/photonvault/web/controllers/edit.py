#encoding=utf8
'''Photo metadata editing'''
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
from photonvault.web.controllers.session import Session
from photonvault.web.models.collection import Item
from photonvault.web.utils.render import render_response
from tornado.web import Controller, URLSpec, RequestHandler, HTTPError
import bson.objectid
import httplib
import iso8601

__docformat__ = 'restructuredtext en'


class Edit(Controller):
	def get_handlers(self):
		return [
			URLSpec('/edit/(.+)', EditSingleHandler),
			URLSpec('/manage/actions', ActionsHandler),
			URLSpec('/manage/actions/([a-zA-Z_]+)', ActionsHandler),
			URLSpec('/manage/list', ListHandler),
		]


class EditSingleHandler(RequestHandler):
	@render_response
	def get(self, str_id):
		obj_id = bson.objectid.ObjectId(str_id)
		result = self.controllers[Database].db[Item.COLLECTION].find_one(
			{'_id': obj_id}
		)
		
		return {
			'_template': 'edit/single.html',
			'title': result[Item.TITLE],
			'description': result.get(Item.DESCRIPTION, ''),
			'date': str(result[Item.DATE]),
			'tags': u'\r\n'.join(result.get(Item.TAGS, [])),
			'id': str_id,
		}
	
	@render_response
	def post(self, str_id):
		obj_id = bson.objectid.ObjectId(str_id)
		
		date_obj = iso8601.parse_date(self.get_argument('date'))
		tag_list = list(sorted(list(
			frozenset(self.get_argument('tags', '').splitlines()))))
		
		self.controllers[Database].db[Item.COLLECTION].update(
			{'_id': obj_id},
			{'$set': {
				Item.TITLE: self.get_argument('title', ''),
				Item.DESCRIPTION: self.get_argument('description', ''),
				Item.DATE: date_obj,
				Item.TAGS: tag_list,
			}}
		)
		
		return {
			'_redirect_url': '/item/%s' % obj_id
		}


class SelectionMixin(object):
	SELECTION_KEY = 'edit_list_selection'
	
	def get_selections(self):
		with self.controllers[Session].session(self) as session:
			return set(session.get(SelectionMixin.SELECTION_KEY, []))
	
	def save_selections(self, id_str_list):
		with self.controllers[Session].session(self) as session:
			session[SelectionMixin.SELECTION_KEY] = id_str_list
	
	def clear_selections(self):
		with self.controllers[Session].session(self) as session:
			session.pop(SelectionMixin.SELECTION_KEY, None)


class ListHandler(RequestHandler, ItemPaginationMixin, SelectionMixin):
	@render_response
	def get(self):
		limit = 100
		count = self.get_item_count()
		results = self.get_paginated_items(limit, reverse_chron=True)
		all_selected_ids = self.get_selections()
		current_ids = frozenset([str(result['_id']) for result in results['items']])
		selected_ids = all_selected_ids & current_ids
		
		return {
			'_template': 'edit/list.html',
			'items': results['items'],
			'paging': {
				'limit': limit,
				'count': count,
				'has_more_older': results['has_more_older'],
				'has_more_newer': results['has_more_newer'],
			},
			'num_selected': len(all_selected_ids),
			'current_ids': list(current_ids),
			'selected_ids': list(selected_ids),
		}
	
	def post(self):
		current_ids = frozenset(self.get_arguments('current_ids'))
		selected_ids = frozenset(self.get_arguments('selection'))
		
		all_selected_ids = self.get_selections()
		all_selected_ids.difference_update(current_ids)
		all_selected_ids.update(selected_ids)
		self.save_selections(list(all_selected_ids))
		
		if self.get_argument('command_older', None):
			self.redirect(
				'/manage/list?older_than=%s' % self.get_argument('older_id'), 
				status=httplib.SEE_OTHER)
		elif self.get_argument('command_newer', None):
			self.redirect(
				'/manage/list?newer_than=%s' % self.get_argument('newer_id'), 
				status=httplib.SEE_OTHER)
		elif self.get_argument('command_clear_selections', None):
			self.clear_selections()
			self.redirect(self.request.uri, status=httplib.SEE_OTHER)
		else:
			self.redirect('/manage/actions', status=httplib.SEE_OTHER)


class ActionsHandler(RequestHandler, SelectionMixin):
	@render_response
	def get(self):
		all_selected_ids = self.get_selections()
		selected_id_list = list(sorted(list(all_selected_ids)))
		first_few_ids = selected_id_list[:5]
		last_few_ids = selected_id_list[max(5, len(selected_id_list) - 5):]
		
		return {
			'_template': 'edit/manage.html',
			'num_selected': len(all_selected_ids),
			'first_few_ids': first_few_ids,
			'last_few_ids': last_few_ids,
		}
	
	def post(self, action):
		all_selected_ids = self.get_selections()
		obj_ids = list([bson.objectid.ObjectId(s) for s in all_selected_ids])
		
		item_collection = self.controllers[Database].db[Item.COLLECTION]
		
		if action == 'edit_date':
			date = iso8601.parse_date(self.get_argument('date'))
			item_collection.update(
				{'_id': {'$in': obj_ids}}, 
				{'$set': {Item.DATE: date}},
				multi=True,
			)
		elif action == 'edit_title':
			item_collection.update(
				{'_id': {'$in': obj_ids}}, 
				{'$set': {Item.TITLE: self.get_argument('title')}},
				multi=True,
			)
		else:
			raise HTTPError(httplib.BAD_REQUEST)
		
		self.redirect('/manage/list', status=httplib.SEE_OTHER)