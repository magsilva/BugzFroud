#!/usr/bin/python

from httplib import *
import re
import os
import os.path
import csv

base_url = "bugzilla.mozilla.org"
# Can be HTTPConnection also
connection = HTTPSConnection( base_url )
connection.connect()

type_re = re.compile( "^text/plain", re.IGNORECASE )
patch_re = re.compile( "(\.diff\"?$|\.patch\"?$)", re.IGNORECASE )
destdir = "bugzilla"

if not os.path.exists( destdir ):
	os.makedirs( destdir )

reader = csv.reader( file( "bugzilla-2005-04-22.csv" ) )
bugs = []
for row in reader:
    bugs.append( int( row[0] ) )

for i in bugs:
	print "\n%d..." %i,
	url = "/attachment.cgi?id=" + str(i)
	real_url = url
	connection.request( "GET", url )
	response = connection.getresponse()

	while response.status in [301, 302]:
		real_url = response.getheader( "Location" )
		connection.request( "GET", real_url )
		response = connection.getresponse()

	if response.status != 200:
		print "%d: %s" % ( response.status, response.reason )
		break

	info = response.getheaders()
	type = response.getheader( "Content-Type" )

	if type_re.search( type ):
		if patch_re.search( type ):
			f = open( "%s/%d.patch" % (destdir,i), "w+" )
			f.write( response.read() )
			f.close()
			f = open( "%s/%d.txt" % (destdir,i), "w+" )
			f.write( "Initial URL: http://%s%s\n" % ( base_url, url ) )
			f.write( "Final URL: http://%s%s\n" % ( base_url, real_url ) )
			for header in info:
				line = "%s: %s\n" % (header)
				f.write( line )
			f.close()
			print "Ok"
		else:
			print "Err, no patch found"
			print info
	else:
		print "Err, no patch found"
		print info

connection.close()
