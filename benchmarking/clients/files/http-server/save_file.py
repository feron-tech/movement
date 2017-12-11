#!/usr/bin/python3
# Authors: Antonis Gotsis (Feron Technologies P.C.)
# Server-side application for HTTP file upload support.
# Inspired by: https://www.tutorialspoint.com/python3/python_cgi_programming.htm

import cgi, os
import cgitb; cgitb.enable()

form = cgi.FieldStorage()

# Get filename here.
fileitem = form['filename']

# Test if the file was uploaded
if fileitem.filename:
   fn = os.path.basename(fileitem.filename)
   open('/tmp/' + fn, 'wb').write(fileitem.file.read())
   message = 'The file "' + fn + '" was uploaded successfully'
else:
   message = 'No file was uploaded'

print ("Content-type:text/html")
print()
print(message
