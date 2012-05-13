#encoding=utf8
'''Session management'''
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
from photonvault.web.models.session import SessionModel
from tornado.web import Controller
import bson.objectid
import contextlib
import datetime
import json
import logging
import threading
import time

__docformat__ = 'restructuredtext en'


_logger = logging.getLogger(__name__)

class SessionCleaner(threading.Thread):
	SLEEP_TIME = 3600 * 3
	
	def __init__(self, controller):
		threading.Thread.__init__(self)
		self.controller = controller
		self.name = 'session_cleaner'
		self.daemon = True
	
	def run(self):
		while True:
			self.controller._remove_old_sessions()
			time.sleep(SessionCleaner.SLEEP_TIME)


class SessionStorage(dict):
	__slots__ = ('id', 'persistent')


class Session(Controller):
	KEY_NAME = 'sid'
	MAX_AGE_DAYS = 40
	
	def init(self):
		self._session_cleaner = SessionCleaner(self)
		self._session_cleaner.start()
	
	def get_handlers(self):
		return []
	
	@contextlib.contextmanager
	def session(self, request, key_name=KEY_NAME):
		collection = self.application.controllers[Database].db[SessionModel.COLLECTION]
		session_id_str = self._get_session_id(request, key_name)
		d = SessionStorage()
		d.id = None
		d.persistent = False
		
		try:
			if session_id_str:
				obj_id = bson.objectid.ObjectId(session_id_str)
				result = collection.find_one({'_id': obj_id})
				
				if result:
					d = SessionStorage(json.loads(result[SessionModel.DATA]))
					d.persistent = result[SessionModel.PERSISTENT]
					d.id = session_id_str
		except Exception:
			_logger.exception('Failed to get session data')
		
		yield d
		
		if not d and d.id:
			collection.remove({'_id': bson.objectid.ObjectId(d.id)})
			return
		
		update_dict = {}
		
		if not d.id \
		or (datetime.datetime.utcnow() - result[SessionModel.COOKIE_DATE]).days > 10 \
		or d.persistent != result[SessionModel.PERSISTENT]:
			if not d.id:
				obj_id = bson.objectid.ObjectId()
				d.id = str(obj_id)
				
			self._save_session_id(request, d.id, d.persistent)
			update_dict[SessionModel.COOKIE_DATE] = datetime.datetime.utcnow()
			update_dict[SessionModel.PERSISTENT] = d.persistent
			
		update_dict[SessionModel.DATA] = json.dumps(d)
		
		collection.update({'_id': obj_id}, {'$set': update_dict}, upsert=True)
		
	def _get_session_id(self, request, key_name=KEY_NAME):
		return request.get_secure_cookie(key_name)
	
	def _save_session_id(self, request, session_id_str, persistent=False, 
	key_name=KEY_NAME):
		request.set_secure_cookie(
			key_name,
			session_id_str,
			expires_days=Session.MAX_AGE_DAYS if persistent else None,
		)
	
	def _remove_old_sessions(self):
		date = datetime.datetime.fromtimestamp(
			time.time() - 3600 * Session.MAX_AGE_DAYS)
		
		self.application.controllers[Database].db[SessionModel.COLLECTION
			].remove({SessionModel.COOKIE_DATE: {'$lt': date}})