#encoding=utf8
'''Rendering functions for Tornado'''

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

__docformat__ = 'restructuredtext en'

import functools
import json

def serialize(obj):
	if isinstance(obj, dict):
		d = {}
		
		for key in obj:
			d[key] = serialize(obj[key])
		
		return d
	
	if isinstance(obj, (list, tuple)):
		l = []
		
		for item in obj:
			l.append(serialize(item))
			
			return l
	
	if isinstance(obj, (int, float, str, unicode)):
		return obj
	
	return unicode(obj)


def render_html_or_json(request_handler, response, template_key='_template',
redirect_key='_redirect'):
	if request_handler.get_argument('_format', None) == 'json':
		request_handler.set_header('Content-Type', 'application/json; encoding=utf-8')
		request_handler.write(json.dumps(serialize(response)))
		request_handler.finish()
		
	elif '%s_url' % redirect_key in response:
		redirect_info = response['%s_url' % redirect_key]
		
		if isinstance(redirect_info, dict):
			request_handler.redirect(
				redirect_info['url'],
				redirect_info.get('permanent', False),
				redirect_info.get('status', None)
			)
		else:
			request_handler.redirect(redirect_info)
		
	else:
		request_handler.render(response[template_key], **response)

def render_response(response_fn, render_fn=render_html_or_json):
	'''Allows a `RequestHandler` to return a `dict` to be rendered 
	
	:parameters:
		response_fn
			The function to decorate
		render_fn
			The function that will be called for rendering. The function
			is passed the request handler instance and the `dict`
	'''
	
	@functools.wraps(response_fn)
	def wrapper(self, *args, **kargs):
		response = response_fn(self, *args, **kargs)
		
		return render_fn(self, response)

	return wrapper