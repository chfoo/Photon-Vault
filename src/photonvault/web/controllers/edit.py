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
from photonvault.web.models.collection import Item
from photonvault.web.utils.render import render_response
from tornado.web import Controller, URLSpec, RequestHandler
import bson.objectid
import iso8601

__docformat__ = 'restructuredtext en'


class Edit(Controller):
	def get_handlers(self):
		return [
			URLSpec('/edit/(.+)', EditSingleHandler),
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