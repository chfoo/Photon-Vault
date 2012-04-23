#encoding=utf8
'''Test database'''
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
from photonvault.tests.web.test_server import ServerBase, post_drop_database, \
	ProductionServerBase
import httplib
import unittest

class TestDatabase(ServerBase):
	@post_drop_database
	def test_upload_image(self):
		'''It should delete the database'''
		pass


class TestProductionDatabase(ProductionServerBase):
	def test_upload_image(self):
		'''It should not delete the database'''
		
		response = self.fetch('/database/drop')
		
		self.assertNotEqual(response.code, httplib.OK)

	
if __name__ == "__main__":
	#import sys;sys.argv = ['', 'Test.testName']
	unittest.main()