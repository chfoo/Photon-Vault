#encoding=utf8

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


from photonvault.web.app import Application
import argparse
import tornado.ioloop
from ConfigParser import ConfigParser

def main():
	arg_parser = argparse.ArgumentParser(
		description=u'Simple web-based photo manager for your home’s LAN.',
	)
	
	arg_parser.add_argument(u'config_filename', metavar=u'CONFIG', type=unicode,
		nargs=1, help=u'The configuration file')
	
	args = arg_parser.parse_args()
	
	application = Application(args.config_filename[0])
	
	config_parser = ConfigParser()
	config_parser.read(args.config_filename)
	
	application.listen(config_parser.getint(u'server', u'port'), 
		config_parser.get(u'server', u'address'))
	tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
	main()