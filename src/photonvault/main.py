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
import logging

log_levels = {
	u'debug': logging.DEBUG,
	u'info': logging.INFO,
	u'warning': logging.WARNING,
	u'error': logging.ERROR,
	u'critical': logging.CRITICAL,
}

def main():
	arg_parser = argparse.ArgumentParser(
		description=u'Simple web-based photo manager for your home’s LAN.',
	)
	
	arg_parser.add_argument(u'config_filename', metavar=u'CONFIG', type=unicode,
		nargs=1, help=u'The configuration file')
	
	args = arg_parser.parse_args()
	
	config_parser = ConfigParser()
	config_parser.read(args.config_filename)
	
	if config_parser.has_option(u'application', u'log_level'):
		level_str = config_parser.get(u'application', u'log_level')
		level = log_levels.get(level_str.lower())
		
		if level:
			logging.basicConfig(level=level)
			logging.debug('Logging enabled')
	
	application = Application(args.config_filename[0])
	
	application.listen(config_parser.getint(u'server', u'port'), 
		config_parser.get(u'server', u'address'))
	tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
	main()