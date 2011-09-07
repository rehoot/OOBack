#!/opt/local/bin/python

# OOBack.py -- python 3+
#
# Purpose:
# 1) Read a configuration file in ~/.OOBack.cfg to get a list
#    of file specifications (with wildcards) to archive. The
#    list does not look recursively into subdirectories.
# 2) Copy selected OpenOffice files to an archive directory,
#    that is specified in the ~/.OOBack.cfg file,
#    unzip each one into its own directory, use git to archive the
#    files that are zipped inside the .odtfiles.
# 3) Assume that the user has already created a directory where 
#    COPIES of OpenOffice files will be sent for archive,
#    and assume that the user has run "git init" and some initial
#    config commands:
# 	   git config −−global user.name YOUR-USERNAME
#   	 git config --glocal user.email YOUREMAIL@YAHOO.COM
# 4) On the first run, the user will be prompted for the name of 
#    the pre-existing archive directory and some path specifications
#    (with optional wildcards) of OpenOffice files to archive 
#    (like ~/Documents/MyNovel/*.odt).
#    The current program does not support recursive file specification,
#    so enter each directory separately.
# 5) After the first run, the ~/.OOBack.cfg config files is read
#    to identify the files to archive
#
# RECOVERY INSTRUCTIONS:
# 1) From the UNIX command line, change directory to be inside 
#    the unzipped directory.
# 2) run a command like this:
#       zip -r ../recovered.odt mimetype .
#    which puts the "mimetype" file first in the zip file and also 
#    zips all the other files in the directory.
# 3) to add (or replace) only the contents.xml file to an existing .odt file:
#       zip ../existing.odt content.xml

import codecs
from configparser import SafeConfigParser
import datetime
import getopt
from glob import glob
import os
import re
import shutil
import stat
import sys

#g_mycodec = 'ISO8859-1'
g_mycodec = 'UTF8'
g_debug_level = 2
g_config_fname = os.path.expanduser('~/.OOBack.cfg')
# global dictionary variables
gd_opts = {}

#
# 
def usage():
	print('usage:\nOOBack.py -c codec')
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
	print('--config-file_name')
	print('-C FILENAME')
	print(' specify an alternate config file that otherwise looks like')
	print(' ~/.OOBack.cfg.  Use this if you want to send sets of OpenOffice')
	print(' files to different archive directories (might be needed if ')
	print(' you have files with the same filename in different directories).')

def main():
	'''main
	1) use getopt to get command-line options
	2) run load options to read ~/.OOBack.cfg
	3) cycle through the file list (including wildcards) and
     unzip the .odt files to allow archiving with git.
	'''
	global g_mycodec
	global g_config_fname

	buf = []
	fname = ''

	# 1) use getopt to get command-line options
	try:
		optlist, args = getopt.getopt(sys.argv[1:] \
			,'vhc:', ['verbose', 'help', 'codec='])
	except (getopt.GetoptError, err):
		print(str(err))
		usage()
		sys.exit(12)
	#
	for o, a in optlist:
		if (o in ['-h', '--help']):
			usage()
			sys.exit()
		elif (o in ['-v', '--verbose']):
			g_debug_level = 6
			pass
		elif o in ['-c', '--codec']:
			g_mycodec = a
		elif o in ['-C', '--config-file-name']:
			g_config_fname = os.path.expanduser(a)
		#
		#

	# 2) run load options to read ~/.OOBack.cfg
	load_options()

	os.chdir(gd_opts['gitdir'])
	os.system('cd ' + gd_opts['gitdir'] + '; rm -R ' \
		+ gd_opts['gitdir'] + '/other')

	#3) cycle through the file list (including wildcards) and
  #   unzip the .odt files to allow archiving with git.
	# 
	for opt_name in gd_opts:
		dprint(2, 'In option loop ******' + repr(opt_name) + ': ' \
			+  repr(gd_opts[opt_name]))
		# The entry in the options list might be a wildcard specification, so 
		# use glob to unglob it:
		if opt_name[0:4] == 'file':
			filelist = glob(gd_opts[opt_name])
		else:
			filelist = []

		if filelist != []:
			dprint(2, 'testing filelist ' + repr(filelist))
			for source_fname in filelist:
				dprint(2, 'testing source_fname ' + repr(source_fname))
				# Find the name of the source OpenOffice file
				###sourcename = os.path.expanduser(gd_opts[d])
				f = os.path.basename(source_fname)
				d = os.path.dirname(source_fname)
				ext = os.path.splitext(f)[1]
				if ext == '.odt':
					# The destination is in a subdirectory of the same name as the file
					destdir = os.path.abspath(gd_opts['gitdir']) + '/' + f
					destfile = destdir + '/' + f
				else:
					# The destination is in a subdirectory of the same name as the file
					destdir = os.path.abspath(gd_opts['gitdir']) + '/other'
					destfile = destdir + '/' + f
					dprint(3, 'dest filename: ' + destfile)
				if os.access(source_fname, os.F_OK):
					if not os.access(destdir, os.F_OK):
						os.mkdir(destdir)
					else:
						# create the directory if it does not exist
						os.system('rm -R ' + destdir)
						os.mkdir(destdir)
		
					# Copy the file into a subdirectory of the same name
					shutil.copy(source_fname, destfile)
					os.chdir(destdir)
					if ext == '.odt':
						os.system('unzip ' + destfile + ' -d ' + destdir)
						# Remove the original .odt file from within 
						# the unzip directory.
						os.remove(destdir + '/' + f)
						# insert EOL into the contents.xml file to make
						# archiving more efficient.  This means that the
						# newline chars must be removed to recover the files.
						expand_contents(destdir + '/content.xml')
				else:
					print('Error, cannot find ' + source_fname)
	
	## run git
	#os.chdir(gd_opts['gitdir'])
	#os.system('git add .')
	#os.system('git add -u .')
	#os.system('git commit -m "auto commit ' \
	#	+ datetime.datetime.now().strftime("%Y %h %d %H:%M:%S") + '"')
	print('')

	

def portpath(pathL):
	'''portpath()
	Given a list object that contains ordered elements of a path 
	or path with filename, join those elements using
	the path separator and return the result.  This might improve
	portability across operating systems.

	Example:
	  portpath(['~','Documents', 'myfile.txt'])
	'''
	return(os.path.normpath(os.path.expanduser(\
				os.path.sep.join(pathL))))

def load_options():
	'''load_options()
	Read /.OOback.cfg and load
	values from two sections: [default] and [archivefiles]  into the
	opts{} dictionary.
	'''
	global gd_opts
	global config_fname
	#
	yn_input = ''

	#
	if(os.access(g_config_fname, os.F_OK)):
		# Create a ConfigParser object:
		parser = SafeConfigParser()
		parser.read([os.path.expanduser(g_config_fname)])
		for sect in parser.sections():
			if sect in ['defaults', 'archivefiles']:
				for o in parser.options(sect):
					# Load all entries from known option sections.
					# This assumes that option names are unique within the file.
					# Variations of this might load required options 
					# one at a time to verify that they exist.
					# This will add multiple dictionaries entry like:
					#    "file1: /Draft/*.odt" 
					# or "gitdir: /D/gits/OO".
					gd_opts.update({o:parser.get(sect, o)})

			else:
				raise Exception('Error, option section not expected: ' + sect)
	else:
		print('Error. The '  + g_config_fname + ' configuration file was ' \
			+ 'not found.')
		yn = input('Do you want to initialize the options? (y/n) ')
		if(yn.upper() == 'Y'):
			setup()
		else:
			print('Quitting without creating option file')
			sys.exit(0)
	#
	# Now cleans the git dir option
	gd_opts.update({gd_opts['gitdir']:os.path.expanduser(gd_opts['gitdir'])})
	
######
#
def setup():
	# create a default options file
	global gd_opts
	global g_config_fname

	try:
		fdo = codecs.open(g_config_fname, 'w', g_mycodec)
	except IOError:
		print('Error.  Cannot open filename: ' + g_config_fname)
		sys.exit(12)

	fdo.write('[defaults]\ngitdir = ')
	gdir = input('Enter the name of the git dir where COPIES of the ' \
		+ 'OpenOffice files will be sent')
	gd_opts.update({'gitdir':gdir})
	fdo.write(gdir + '\n\n[archivefiles]\n')

	# Add code here to check for the .git directory or for a valid
	# git repository.  Maybe run git init if need be.

	fspec = ''
	fcount = 0
	while fspec.upper() != 'Q':
		fspec = input('Enter the full path and optional wildcard for ' \
			+ 'OpenOffice files to track, or Q to quit:')
		if fspec.upper() != 'Q' and len(fspec) > 0:
			fcount += 1
			opt_name = 'file' + str(fcount)
			gd_opts.update({opt_name: fspec})
			fdo.write(opt_name + ' = ' + fspec + '\n')
			fspec = ''

	fdo.close
	print(repr(gd_opts))
	yn = input('Do the files specifications above look correct? (y/n)')
	if yn.upper() == 'N':
		raise Exception('user rejected the default options')
	print('Now examine ' + conf_file_name + ' to see if it looks OK.')
	#yn = input('press any key to continue archiving')	
	print('This processed the file specifications in ' + g_config_fname)

#
def expand_contents(fname):
	# open a contents.xml file,
	# expand a few tags to insert new lines
	global  g_mycodec

	buff = []

	try:
		fcontents = codecs.open(fname, 'r', g_mycodec)
	except IOError:
		raise Exception("file not found " + fname)
	for s in fcontents:
		buff.append(s)
	fcontents.close

	for j in range(len(buff)):
		buff[j] = re.sub(re.compile(' xmlns[:]'), '\nxmlns:', buff[j])
		buff[j] = re.sub(re.compile('[<]text[:]'), '\n<text:', buff[j])
		buff[j] = re.sub(re.compile('[<]style[:]'), '\n<style:', buff[j])

	dprint(4, 'The buffer is now: ' + repr(buff))
	fo = codecs.open(fname, 'w', g_mycodec)
	for j in range(len(buff)):
		fo.write(buff[j])
	
#
def dprint(dbglevel, txt):
	global g_debug_level
	#
	if(dbglevel <= g_debug_level):
		print(txt,file=sys.stderr)

if __name__ == '__main__':
	main()
