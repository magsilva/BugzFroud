#!/usr/bin/python

from urllib2 import *
import re
import os
import os.path

base_url = "http://bugzilla.mozilla.org"
type_re = re.compile( "^text/plain", re.IGNORECASE )
patch_re = re.compile( "(\.diff\"?$|\.patch\"?$)", re.IGNORECASE )
destdir = "mozilla"

if not os.path.exists( destdir ):
	os.makedirs( destdir )


# for i in range(177269,177270):
for i in range(1,291100):
	print "\n%d..." %i,
	url = base_url + "/attachment.cgi?id=" + str(i)
	attachment = urlopen( url )
	info = attachment.info()
	type = info[ "Content-Type" ]

	if type_re.search( type ):
		if patch_re.search( type ):
			f = open( "%s/%d.patch" % (destdir,i), "w+" )
			f.write( attachment.read() )
			f.close()
			f = open( "%s/%d.txt" % (destdir,i), "w+" )
			f.write( "URL: " + url + "\n" )
			f.write( str( info ) )
			f.close()
			print "Ok"
		else:
			print "No patch found"
	else:
		print "No patch found"
