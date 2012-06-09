#!/usr/bin/python
"""A basic transparent HTTP proxy"""

__author__ = "Erik Johansson"
__email__  = "erik@ejohansson.se"
__license__= """
Copyright (c) 2012 Erik Johansson <erik@ejohansson.se>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
USA

"""

from twisted.web import http
from twisted.internet import reactor, protocol
from twisted.python import log
from twisted.internet.error import CannotListenError

import re
import sys
import sqlite3
import datetime
import time
from StringIO import StringIO
import gzip
import urlparse
import os

if not os.path.exists('proxy_log'):
	os.makedirs('proxy_log')


log_filename = os.path.join(os.path.abspath('.'), 'proxy_log', ('%s.log' % sys.argv[1]))
log.startLogging(open(log_filename, 'wt'))

class ProxyClient(http.HTTPClient):
	""" The proxy client connects to the real server, fetches the resource and
	sends it back to the original client, possibly in a slightly different
	form.
	"""

	def __init__(self, method, uri, postData, headers, originalRequest):
		with open('inject.html', 'rt') as read_buffer:
			self.script_html = read_buffer.read()

		self.method = method
		self.uri = uri
		#self.uri = uri_parse[2]

		self.postData = postData
		self.headers = headers # originalRequest.headers
		self.responseHeaders = {}
		self.originalRequest = originalRequest
		self.browserHeaders = {}
		self.contentLength = None
		self.contentType = ''
		self.gzip = False
		self.referrer = ''




	def sendRequest(self):
		#log.msg("Sending request: %s %s" % (self.method, self.uri))
		uri_parse = urlparse.urlparse(self.uri)
		#self.sendCommand(self.method, self.uri)
		self.sendCommand(self.method, uri_parse[2])




	def sendHeaders(self):
		for key, values in self.headers:
			if key.lower() == 'referer' or key.lower() == 'referrer':
				self.referrer = values[0]

			if key.lower() == 'connection':
				values = ['close']
			elif key.lower() == 'keep-alive':
				next

			for value in values:
				self.sendHeader(key, value)
			#if key.lower() == 'connection':
			#	values = ['close']
			#elif key.lower() == 'proxy-connection':
			#	values = ['']

			#for value in values:
			#	self.sendHeader(key, value)
			#	log.msg('\t%s: %s'  % (key, value))

			self.browserHeaders[key] = values
		self.endHeaders()




	#def sendCommand(self, command, path):
	#	self.transport.write('%s %s HTTP/1.0\r\n' % (command, path))
	#	log.msg('%s %s HTTP/1.0\r\n' % (command, path))

	def sendPostData(self):
		log.msg("Sending POST data")
		self.transport.write(self.postData)

	def connectionMade(self):
		log.msg("HTTP connection made")
		self.sendRequest()
		self.sendHeaders()
		if self.method == 'POST':
			self.sendPostData()




	def handleStatus(self, version, code, message):
		log.msg("Got server response: %s %s %s" % (version, code, message))
		self.originalRequest.setResponseCode(int(code), message)




	def handleHeader(self, key, value):
		if key.lower() == 'content-encoding':
			if value.lower() == 'gzip':
				self.gzip = True
				return

		if key.lower() == 'content-type':
			self.contentType = value

		#if key.lower() == 'content-length':
		#	value = int(value) + len(self.script_html)
		#	self.contentLength = value

		self.originalRequest.responseHeaders.addRawHeader(key, value)
		self.responseHeaders[key] = value



	def handleResponse(self, data):
		if self.gzip:
			buf = StringIO(data)
			f = gzip.GzipFile(fileobj=buf)
			data = f.read()

		if self.contentType.find('text/html') != -1:
			log.msg('\033[95mContent Type %s\033[0m. Inserting script.' % self.contentType)
			data = data.replace('</body>', self.script_html + '</body>')
			self.contentLength = len(data)

		self.data = self.originalRequest.processResponse(data)

		if self.contentLength != None:
			self.originalRequest.setHeader('Content-Length', self.contentLength)

		self.originalRequest.write(self.data)
		self.originalRequest.finish()
		self.transport.loseConnection()

		self.db_save()




	def db_save(self):
		data_buffer = ''
		try:
			data_buffer = self.data.decode('latin-1')
		except Exception, ex:
			log.msg(self.uri)
			log.msg(ex)

		connection = sqlite3.connect('database/db.sql')
		cursor = connection.cursor()
		cursor.execute('insert into interface_activity (date_time, ip_address, method, uri, post_data, response_headers, response, headers, activity_type, test_suite_id, referrer) values (?,?,?,?,?,?,?,?,?,?,?)', (
				datetime.datetime.now(),
				self.originalRequest.getClientIP(),
				self.method,
				self.uri,
				self.postData,
				repr(self.responseHeaders),
				data_buffer,
				repr(self.browserHeaders),
				'user',
				int(sys.argv[1]),
				self.referrer,
			)
		)
		connection.commit()
		connection.close()




class ProxyClientFactory(protocol.ClientFactory):
	def __init__(self, method, uri, postData, headers, originalRequest):
		self.protocol = ProxyClient
		self.method = method
		self.uri = uri
		self.postData = postData
		self.headers = headers
		self.originalRequest = originalRequest

	def buildProtocol(self, addr):
		return self.protocol(self.method, self.uri, self.postData, self.headers, self.originalRequest)

	def clientConnectionFailed(self, connector, reason):
		log.err("Server connection failed: %s" % reason)
		self.originalRequest.setResponseCode(504)
		self.originalRequest.finish()




class ProxyRequest(http.Request):
	def __init__(self, channel, queued, reactor=reactor):
		http.Request.__init__(self, channel, queued)
		self.reactor = reactor

	def process(self):
		host = self.getHeader('host')
		if not host:
			log.err("No host header given")
			self.setResponseCode(400)
			self.finish()
			return

		port = 80
		if ':' in host:
			host, port = host.split(':')
			port = int(port)

		log.msg('\033[95mhost: %s %s\033[0m' % (self.uri, port))

		#if self.uri.find('feed_growl') != -1:
		#	return

		self.setHost(host, port)
		self.content.seek(0, 0)
		self.postData = self.content.read()

		if(self.uri.endswith('/roadmap/assert.html')):
			self.processAssert()
			return

		factory = ProxyClientFactory(
			self.method,
			self.uri,
			self.postData,
			self.requestHeaders.getAllRawHeaders(),
			self
		)
		self.reactor.connectTCP(host, port, factory)

	def processAssert(self):
		header_package = {}
		referrer = ''

		for key, values in self.requestHeaders.getAllRawHeaders():
			header_package[key] = values

			if key.lower() == 'referer' or key.lower() == 'referrer':
				referrer = values[0]

		connection = sqlite3.connect('database/db.sql')
		cursor = connection.cursor()
		cursor.execute('insert into interface_activity (date_time, ip_address, method, uri, post_data, headers, activity_type, response, response_headers, test_suite_id, referrer) values (?,?,?,?,?,?,?,?,?,?,?)', (
				datetime.datetime.now(),
				str(self),
				self.method,
				self.uri,
				self.postData,
				repr(header_package),
				'assert',
				'',
				'',
				int(sys.argv[1]),
				referrer,
			)
		)
		connection.commit()
		connection.close()

		# return a 200
		log.msg('\033[95mNEED TO RETURN 200 here\033[0m')
		self.setHeader('Content-Type', 'text/plain')
		self.write('success\n')
		self.finish()

	def processResponse(self, data):
		return data




class TransparentProxy(http.HTTPChannel):
	requestFactory = ProxyRequest

class ProxyFactory(http.HTTPFactory):
	protocol = TransparentProxy

free_port = 9000
success = False

while not success:
	try:
		reactor.listenTCP(free_port, ProxyFactory(), 50, '10.211.55.7')
		log.msg('#############################################################################')
		log.msg('#                                                                           ')
		log.msg('#   Starting test server                                                    ')
		log.msg('#                                                                           ')
		log.msg('#   Set your proxy server settings to: %s port %s                           ' % ('10.211.55.7', free_port))
		log.msg('#                                                                           ')
		log.msg('#############################################################################')
		reactor.run()
		success = True
	except CannotListenError:
		free_port += 1