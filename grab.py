#!/usr/bin/python

from httplib import *
import xml.dom.minidom as dom
import re
import os
import os.path
import csv
import sys
import HTMLParser


class PatchExtractor(object):

	def __init__( self ):
		self.type_regexp = re.compile( "^text/plain", re.IGNORECASE )
		self.patch_regexp = re.compile( "(\.diff\"?$|\.patch\"?$)", re.IGNORECASE )
		self.patchid_regexp = re.compile( "<attachid>(\d+)</attachid>" )
		self.destdir = "attachments"


	def set_url( self, url ):
		"""Set the connection. It expects a full URL specifier (protocol://address)"""

		# Strip the protocol (if any specified)
		try:
			self.protocol = url[:url.rindex( "//" )-1]
			url = url[url.rindex( "//" ) + 2:]
		except ValueError:
			self.protocol = "http"
			pass

		# Split the hostname from the pathname
		try:
			host = url[:url.index( "/" )]
			path = url[url.index( "/" ):]
		except ValueError:
			host = url
			path = ""

		self.host = host
		self.path = path

	
	def set_destdir( self, directory ):
		self.destdir = directory
		if not os.path.exists( self.destdir ):
			os.makedirs( self.destdir )


	def start( self, csv_file, start = 1, end = 0 ):
		"""Start to harvest the bugs. It expects a CSV file which first column holds the bug id"""
		reader = csv.reader( file( csv_file ) )
		bugs = []
		for row in reader:
			bugs.append( int( row[0] ) )
		bugs.sort()

		if end == 0:
			end = bugs[-1:]

		self._connect()
		for i in bugs:
			if i >= start and i <= end:
				self._process_bug( i )

		self.connection.close()


	def _connect( self ):
		try:
			self.connection.close()
		except AttributeError:
			pass

		if self.protocol == "https":
			self.connection = HTTPSConnection( self.host )
		elif self.protocol == "http":
			self.connection = HTTPConnection( self.host )
		else:
			self.connection = HTTPConnection( self.host )

		self.connection.connect()


		# Redirects
#		self.connection.request( "GET", self.path )
#		response = self.connection.getresponse()
#
#		while response.status in [301, 302]:
#			self.set_url( response.getheader( "Location" ) )
#			self.connection.request( "GET", self.path )
#			response = self.connection.getresponse()
#
#		if response.status != 200:
#			print "%d: %s" % ( response.status, response.reason )

	
	def _process_bug( self, bugid ):
		print "\nBug %d..." % bugid,
		url = "%s/show_bug.cgi?ctype=xml&id=%d" % ( self.path, bugid )

		self.connection.request( "GET", url )
		response = self.connection.getresponse()

		data = response.read()
		filename = "%s/bug-%d.xml" % ( self.destdir, bugid )
		f = open( filename, "w+" )
		f.write( data )
		f.close()

		attachments = []
		try:	
			xml = dom.parseString( data )

			for attachidElement in xml.getElementsByTagName( "attachid" ):
				attachments.append( int( attachidElement.childNodes[0].data ) )

			print "\nOk"
		except:
			print "\nErr, XML document not well-formed"
			os.rename( filename, filename + ".err" )

			# Let's try a regexp
			print "\n\tTrying some heuristics to discover the attachment's id...",
			for attachid in self.patchid_regexp.findall( data ):
				print ( " %d" % int( attachid ) ),
				attachments.append( int( attachid ) )

		for attachid in attachments:
				self._process_attachment( attachid )



	def _process_attachment( self, attachid ):
		print "\n\tAttachment %d..." % attachid,
		url = "%s/attachment.cgi?id=%d" % ( self.path, attachid )
	
		self.connection.request( "GET", url )
		response = self.connection.getresponse()

		info = response.getheaders()
		type = response.getheader( "Content-Type" )

		suffix = ""
		if not self.type_regexp.search( type ):
			print "Err, no patch found (type mismatch)"
			suffix = ".err1"
		elif not self.patch_regexp.search( type ):
			print "Err, no patch found (is text but not a patch)"
			suffix = ".err2"
		else:
			print "Ok"

		f = open( "%s/%d.patch%s" % ( self.destdir, attachid, suffix ), "w+" )
		f.write( response.read() )
		f.close()
		f = open( "%s/%d.txt" % ( self.destdir, attachid ), "w+" )
		f.write( "URL: http://%s%s\n" % ( self.host, url ) )
		for header in info:
			line = "%s: %s\n" % header
			f.write( line )
		f.close()


def main( args ):
	extractor = PatchExtractor()
	extractor.set_url( args[0] )
	extractor.set_destdir( args[1] )
	try:
		extractor.start( args[2], int( args[3] ), int( args[4] ) )
	except IndexError:
		try:
			extractor.start( args[2], int( args[3] ) )
		except IndexError:
			extractor.start( args[2] )


if __name__ == "__main__":
	main( sys.argv[1:] )
