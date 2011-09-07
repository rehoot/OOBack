#!/usr/bin/env python
# OORecov.py: Python 3.2
#
# Read a directory that contains an unzipped OpenOffice .odt
# file that has been modified by OOBack.py.
# Remove the extra EOL markers that were added by OOBack.py,
# then zip the directory to make it a real .odt file.
import codecs
import getopt
import os
import re
import sys

#g_mycodec = 'ISO8859-1'
g_mycodec = 'UTF8'
g_debug_level = 6

def usage():
	print('usage:\nOORecov.py -f filename -c codec')
	print('--verbose')
	print('-v')
	print('	display lots of info about what the program is doing.')
	print('--help')
	print('-h')
	print('	this help message.')
	print('--codec=')
	print('-c CODEC')
	print('	the codec for the input file, such as --codec ISO8859-1')
	print('	or maybe utf8.  Gutenberge text files should have a line')
	print('	near the top that specifies the codec.')
	print('--filename=')
	print('-f FNAME')
	print('	the filename of directory that contains the ' \
		+ 'unzipped OpenOffice files')

def main():
	'''This will eventually be a replacement for my
	various emacs macros that scan my LaTeX documents
	for errors.
	'''
	global g_mycodec
	buff = []
	new_buff = []
	dirname = ''
	try:
		optlist, args = getopt.getopt(sys.argv[1:] \
			,'vhc:f:', ['verbose', 'help', 'codec=', 'file='])
	except (getopt.GetoptError, err):
		print(str(err))
		usage()
		sys.exit(12)
	#
	for o, a in optlist:
		if (o in ('-h', '--help')):
			usage()
			sys.exit()
		elif (o in ('-v', '--verbose')):
			g_debug_level = 6
			pass
		elif o in ('-c', '--codec'):
			g_mycodec = a
		elif o in ('-f', '--filename'):
			dirname = os.path.abspath(os.path.expanduser(a))
			fname = os.path.normpath(dirname + '/content.xml')
			os.chdir(dirname)
	
		#
	# Confirm that a filename was passed.
	if dirname == '':
		usage()
		sys.exit()
		#

	# Remove the quarantine on files tha are unzipped
	os.system('xattr -d com.apple.quarantine ' + fname)

	try:
		fd1 = codecs.open(fname , 'r', g_mycodec)
	except IOError:
		print('Error: Cannot open filename: ' + fname)
		sys.exit(12)
	dprint(1, 'after open')
	rows = 0
	# Read the input file
	for s in fd1:
		buff.append(s)
		rows += 1
	dprint(1, 'Input lines read: ' + str(rows))
	fd1.close

	# Remove the extra newlines that were added by OOBack.py.
	# This process should be harmless to files that do not 
	# contain the extra newlines. 
	for j in range(len(buff)):
		##	buff[j] = re.sub(re.compile('\nxmlns[:]'), 'xmlns:', buff[j])
		##	buff[j] = re.sub(re.compile('\n[<]text[:]'), '<text:', buff[j])
		##	buff[j] = re.sub(re.compile('\n[<]style[:]'), '<style:', buff[j])

		# merge rows where needed
		if buff[j][0:6] == '<text:' \
		or buff[j][0:7] == '<style:' \
		or buff[j][0:6] == 'xmlns:':
			new_buff[-1] += ' ' + buff[j].rstrip('\n')
		else:
			new_buff.append(buff[j])
	
	dprint(4, 'The buffer is now: ' + repr(new_buff))
	fo = codecs.open(fname, 'w', g_mycodec)
	for j in range(len(new_buff)):
		fo.write(new_buff[j])
	fo.close

	# now zip the directory
	os.system('zip -r ' + os.path.normpath(os.path.dirname(dirname) + '/RECOV' \
		+ os.path.basename(dirname))  + ' mimetype .')

#
def dprint(dbglevel, txt):
	global g_debug_level
	#
	if(dbglevel <= g_debug_level):
		print(txt,file=sys.stderr)

if __name__ == '__main__':
	main()
