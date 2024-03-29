#encoding=utf8
'''Collection model'''

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


class Item(object):
	COLLECTION = 'items'
	TITLE = 'title'
	DESCRIPTION = 'description'
	TAGS = 'tags'
	DATE = 'date'
	FILE_ID = 'file_id'
	FINGERPRINT = 'fingerprint'


class UploadQueue(object):
	COLLECTION = 'upload_queue'
	FILE_ID = 'file_id'


class Thumbnail(object):
	COLLECTION = 'thumbnails'
	SIZES = 'sizes'
	
	class Size(object):
		TIME = 'time'
		DATA = 'data'