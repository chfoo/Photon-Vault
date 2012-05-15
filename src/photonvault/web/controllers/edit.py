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
from photonvault.web.controllers.base.handler import BaseHandler
from photonvault.web.controllers.database import Database
from photonvault.web.controllers.mixins.items import ItemPaginationMixin
from photonvault.web.controllers.session import Session
from photonvault.web.models.collection import Item, Thumbnail
from photonvault.web.utils.render import render_response
from tornado.web import Controller, URLSpec, HTTPError
import PIL.Image
import bson.objectid
import datetime
import httplib
import iso8601
import os
import photonvault.utils.exif
import pyexiv2.metadata
import shutil
import tempfile
import pymongo

__docformat__ = 'restructuredtext en'


class Edit(Controller):
	def get_handlers(self):
		return [
			URLSpec('/edit/(.+)', EditSingleHandler),
			URLSpec('/manage/actions', ActionsHandler),
			URLSpec('/manage/actions/([a-zA-Z_]+)', ActionsHandler),
			URLSpec('/manage/list', ListHandler),
			URLSpec('/manage/delete_tag', DeleteTagHandler),
			URLSpec('/manage/rename_tag', RenameTagHandler),
			URLSpec('/tools', ToolsHandler),
		]


class EXIFMixin(object):
	def get_orientation(self, file_id, filter_include=(1, 3, 6, 8)):
		file_obj = self.controllers[Database].fs.get(file_id)
		pil_image = PIL.Image.open(file_obj) 
		
		value = photonvault.utils.exif.get_orientation_quick(pil_image)
		
		if filter_include:
			if value in filter_include:
				return value
		else:
			return value
	
	def apply_exif(self, item_id, key_value_dict):
		result = self.controllers[Database].db[Item.COLLECTION].find_one(
			{'_id': item_id}
		)
		
		file_id = result[Item.FILE_ID]
		file_obj = self.controllers[Database].fs.get(file_id)
		
		temp_file_obj = tempfile.NamedTemporaryFile(delete=False)
		shutil.copyfileobj(file_obj, temp_file_obj)
		temp_file_obj.close()
		
		metadata = pyexiv2.metadata.ImageMetadata(temp_file_obj.name)
		metadata.read()
		
		for k, v in key_value_dict.iteritems():
			metadata[k] = v
		
		metadata.write()
		
		dest_file_obj = self.controllers[Database].fs.new_file()
		dest_file_obj.filename = file_obj.filename
		dest_file_obj.content_type = file_obj.content_type
		
		shutil.copyfileobj(open(temp_file_obj.name, 'rb'), dest_file_obj)
		dest_file_obj.close()
		
		self.controllers[Database].db[Item.COLLECTION].update(
			{'_id': item_id},
			{'$set': {Item.FILE_ID: dest_file_obj._id}}
		)
		
		self.controllers[Database].fs.delete(file_id)
		os.remove(temp_file_obj.name)

class EditSingleHandler(BaseHandler, EXIFMixin):
	@render_response
	def get(self, str_id):
		obj_id = bson.objectid.ObjectId(str_id)
		result = self.controllers[Database].db[Item.COLLECTION].find_one(
			{'_id': obj_id}
		)
		
		orientation = self.get_orientation(result[Item.FILE_ID])
		
		return {
			'_template': 'edit/single.html',
			'title': result[Item.TITLE],
			'description': result.get(Item.DESCRIPTION, ''),
			'date': str(result[Item.DATE]),
			'tags': u'\r\n'.join(result.get(Item.TAGS, [])),
			'id': str_id,
			'orientation': orientation,
		}
	
	@render_response
	def post(self, str_id):
		obj_id = bson.objectid.ObjectId(str_id)
		date_obj = iso8601.parse_date(self.get_argument('date'))
		exif_dict = {
			'Exif.Photo.DateTimeOriginal': date_obj,
			'Xmp.photoshop.DateCreated': date_obj,
		}
		tag_list = list(sorted(list(
			frozenset(self.get_argument('tags', '').splitlines()))))
		
		if self.get_argument('orientation', None):
			exif_dict['Exif.Image.Orientation'] = int(self.get_argument('orientation'))
			exif_dict['Xmp.tiff.Orientation'] = int(self.get_argument('orientation'))
			
			# Invalidate thumbnail
			self.controllers[Database].db[Thumbnail.COLLECTION].remove({'_id': obj_id})
		
		self.apply_exif(obj_id, exif_dict)
		
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


class ListHandler(BaseHandler, ItemPaginationMixin, SelectionMixin):
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
			'earliest_year': self.get_earliest_year(),
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
		elif self.get_argument('command_jump_to_year', None):
			date_obj = datetime.datetime(int(self.get_argument('year')) + 1, 1, 1)
		
			result = self.controllers[Database].db[Item.COLLECTION].find_one(
				{Item.DATE: {'$lte': date_obj}},
				sort=[(Item.DATE, pymongo.DESCENDING), ('_id', pymongo.DESCENDING)]
			)
			
			self.redirect(
				'/manage/list?older_than=%s' % result['_id'], 
				status=httplib.SEE_OTHER)
		else:
			self.redirect('/manage/actions', status=httplib.SEE_OTHER)


class ActionsHandler(BaseHandler, SelectionMixin, EXIFMixin):
	@render_response
	def get(self):
		all_selected_ids = self.get_selections()
		selected_id_list = list(sorted(list(all_selected_ids)))
		first_few_ids = selected_id_list[:5]
		last_few_ids = selected_id_list[max(5, len(selected_id_list) - 5):]
		tags = self.controllers[Database].db[Item.COLLECTION].distinct(
			Item.TAGS)
		
		return {
			'_template': 'edit/manage.html',
			'num_selected': len(all_selected_ids),
			'first_few_ids': first_few_ids,
			'last_few_ids': last_few_ids,
			'tags': tags,
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
			
			for obj_id in obj_ids:
				self.apply_exif(obj_id, {
					'Exif.Photo.DateTimeOriginal': date,
					'Xmp.photoshop.DateCreated': date,
				})
			
		elif action == 'edit_title':
			item_collection.update(
				{'_id': {'$in': obj_ids}}, 
				{'$set': {Item.TITLE: self.get_argument('title')}},
				multi=True,
			)
		elif action == 'add_tag':
			item_collection.update(
				{'_id': {'$in': obj_ids}}, 
				{'$addToSet': {Item.TAGS: self.get_argument('tag')}},
				multi=True,
			)
		elif action == 'remove_tag':
			item_collection.update(
				{'_id': {'$in': obj_ids}}, 
				{'$pull': {Item.TAGS: self.get_argument('tag')}},
				multi=True,
			)
		elif action == 'set_orientation':
			orientation = int(self.get_argument('orientation'))
			
			for obj_id in obj_ids:
				self.apply_exif(obj_id, {
					'Exif.Image.Orientation': orientation,
					'Xmp.tiff.Orientation': orientation,
				})
				# Invalidate thumbnail
				self.controllers[Database].db[Thumbnail.COLLECTION].remove({'_id': obj_id})
		elif action == 'delete' and self.get_argument('delete', None) == 'delete':
			for obj_id in obj_ids:
				item = item_collection.find_one({'_id': obj_id})
				self.controllers[Database].fs.delete(item[Item.FILE_ID])
				item_collection.remove({'_id': obj_id})
		
			self.clear_selections()
		else:
			raise HTTPError(httplib.BAD_REQUEST)
		
		self.redirect('/manage/list', status=httplib.SEE_OTHER)


class DeleteTagHandler(BaseHandler):
	@render_response
	def get(self):
		tags = self.controllers[Database].db[Item.COLLECTION].distinct(
			Item.TAGS)
		return {
			'_template': 'edit/delete_tag.html',
			'tags': tags
		}
	
	def post(self):
		tag = self.get_argument('tag')
		
		self.controllers[Database].db[Item.COLLECTION].update(
			{Item.TAGS: tag},
			{'$pull': {Item.TAGS: tag}},
			multi=True
		)
		
		self.redirect('/all_tags', status=httplib.SEE_OTHER)
	

class RenameTagHandler(BaseHandler):
	@render_response
	def get(self):
		tags = self.controllers[Database].db[Item.COLLECTION].distinct(
			Item.TAGS)
		return {
			'_template': 'edit/rename_tag.html',
			'tags': tags
		}
	
	def post(self):
		old_tag = self.get_argument('old_tag')
		new_tag = self.get_argument('new_tag')
		
		self.controllers[Database].db[Item.COLLECTION].update(
			{Item.TAGS: old_tag},
			{'$addToSet': {Item.TAGS: new_tag}},
			multi=True
		)
		self.controllers[Database].db[Item.COLLECTION].update(
			{Item.TAGS: old_tag},
			{'$pull': {Item.TAGS: old_tag}},
			multi=True
		)
		
		self.redirect('/all_tags', status=httplib.SEE_OTHER)
		

class ToolsHandler(BaseHandler):
	@render_response
	def get(self):
		return {
			'_template': 'edit/tools.html',
		}