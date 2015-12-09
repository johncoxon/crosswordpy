#!/usr/bin/env python
# encoding: utf-8
"""
A module which, on import, yields functions for automatically printing the Guardian crossword.
Based on a Python script written by Jonny Nichols (University of Leicester) in the dim past.

Author:	John Coxon, Space Environment Physics group, University of Southampton
Date:	2015/02/27
"""

import datetime, inspect, os, urllib2, ConfigParser, crossword as cw

# Note that there is code at the bottom of this file, after the functions are defined, which runs
# upon the module being imported.

#---------------------------------------------------------------------------------------------------

def preferences(printerName, username, fitplot = True, ghostscript = True, pdfcrop = True,
	PyPDF2 = True):
	"""
	Saves user preferences connected to dependencies, the name and features of the desired printer,
	and the username of the user (for use in recording crossword progress).
	"""

	config = ConfigParser.SafeConfigParser()

	# Set up the printer preferences.
	config.add_section('Printer')
	config.set('Printer', 'Name', printerName)
	config.set('Printer', 'fitplot', str(fitplot))

	config.add_section('Dependencies')
	config.set('Dependencies', 'ghostscript', str(ghostscript))
	config.set('Dependencies', 'pdfcrop', str(pdfcrop))
	config.set('Dependencies', 'PyPDF2', str(PyPDF2))

	config.add_section('Installation')
	config.set('Installation', 'Username', username)

	# Save the preferences back to a file.
	# This is done in a somewhat archaic way because ion doesn't have Python 2.5+...
	prefs_file = open(os.path.dirname(__file__) + '/preferences.cfg', 'wb')

	try:
		config.write(preferences)
	finally:
		prefs_file.close()

	cw.fitplot = fitplot
	cw.ghostscript = ghostscript
	cw.pdfcrop = pdfcrop
	cw.PyPDF2 = PyPDF2
	cw.printer = printerName
	cw.username = username

#---------------------------------------------------------------------------------------------------

def get_saturday_xword_no():
	"""
	Gets the number of last Saturday's crossword by getting today's number and subtracting.
	Takes account of situations in which Christmas Day will screw up the mathematics.
	"""
	
	# Get the current date and day of week.
	today = datetime.date.today()
	weekday = today.weekday()

	# Get the date on Saturday.
	saturday = today - datetime.timedelta(weekday + 2)

	# Get today's crossword number.
	_, todayxwordno = get_xword_url()

	# Get Christmas Day as a datetime object.
	xmas = datetime.date(saturday.year, 12, 25)

	# Subract to get Saturday's crossword number.
	# If the two are on opposite sides of Christmas Day, subtract one less from today's xwordno.
	if (today > xmas) & (saturday < xmas) & (xmas.weekday() != 6):
		xwordno = todayxwordno - weekday
	else:		
		xwordno = todayxwordno - (weekday + 1)

	return xwordno
	
#---------------------------------------------------------------------------------------------------

def next_xword_no(user):
	"""
	Get the next number needed for the crossword.

	INPUTS
		user: The username for which the directory should be inspected.
	"""

	# Get the list of files from the archive directory and sort them.
	files = os.listdir(os.path.dirname(inspect.getfile(inspect.currentframe())) + '/archive')
	files.sort()
	
	try:
		# Get the number of files and then select the last file in the list.
		xwordno = files[-1]

		# Get the start of the filename and add 1 to get the next crossword desired.
		xwordno = int(xwordno[:5]) + 1		
	except:
		# If this does not work, 12395 is the first crossword for which there is a PDF.
		xwordno = 12395
		
	return xwordno

#---------------------------------------------------------------------------------------------------

def get_xword_url(xwordno = 0):
	"""
	Gets the Quick Crossword URL from the HTML (from the crossword number if specified).

	OPTIONAL INPUTS
		xwordno: The crossword number to get the URL from.
	"""

	if xwordno == 0:
		cw_url = 'http://www.theguardian.com/crosswords/'
		try:
			response = urllib2.urlopen(cw_url)
		except urllib2.HTTPError:
			print('Error when accessing: ' + cw_url)
			raise
		cw_html = response.read()
		cw_search = 'http://www.theguardian.com/crosswords/quick/'
		cw_loc = cw_html.find(cw_search) + len(cw_search)
		if cw_loc != -1:
			xwordno = int(cw_html[cw_loc:cw_loc+5])
			actualxwordno = xwordno

	url = 'http://www.theguardian.com/crosswords/quick/' + str(xwordno)
	print url

	try:
		response = urllib2.urlopen(url)
	except urllib2.HTTPError:
		print('Error when accessing: ' + url)
		raise

	html = response.read()
	
	pdf_search = '>PDF'
	pdf_loc = html.find(pdf_search)
	if pdf_loc != -1:
		pdf_url_str = html[pdf_loc-80:pdf_loc]
	else:
		raise StandardError('No PDF was found in the HTML of the page.')
	
	strsplit = pdf_url_str.split('"')
	
	foundURL = False

	for substr in strsplit: 
		if substr[0] == 'h':
			pdfurl = substr
			foundURL = True
			break

	if foundURL == False:
		pdfurl, actualxwordno = get_xword_url(xwordno = xwordno + 1)
	else:
		actualxwordno = xwordno

	return pdfurl, actualxwordno

#---------------------------------------------------------------------------------------------------

def download_pdf(pdfurl, saturday = False, archive = False):
	"""
	Download the PDF and save to a local file.

	INPUTS
		pdfurl: The URL to download from.

	OPTIONAL INPUTS
		saturday: Set this to download the Saturday crossword.
		archive: Set this to download an old crossword.
	"""
	
	response = urllib2.urlopen(pdfurl)
	if saturday != False:
		filename = '/saturday.pdf'
	elif archive != False:
		filename = '/archive/' + str(archive) + '.pdf'
	else:
		filename = '/today.pdf'
		
	pdffile = os.path.dirname(inspect.getfile(inspect.currentframe())) + filename
	localFile = open(pdffile, 'w')
	localFile.write(response.read())
	
	return pdffile

#---------------------------------------------------------------------------------------------------
	
def crop_pdf(pdffile, pdfcrop = True, ghostscript = True):
	"""
	Crop the local PDF file to remove the large margins, using pdfcrop and ghostscript.

	INPUTS
		pdffile: The PDF file to be cropped.
	"""
	
	# Get just the path and basename, not the extension.
	filename = os.path.splitext(pdffile)[0]

	# Crop the pdf.
	if pdfcrop == True:
		os.popen('pdfcrop --margins 10 {0}'.format(pdffile))
	else:
		os.popen('cp {0} {1}-crop.pdf'.format(pdffile, filename))

	# Expand the PDF to an A4 page.
	if ghostscript == True:
		gsParams = '-sDEVICE=pdfwrite -sPAPERSIZE=a4 -dFIXEDMEDIA -dPDFFitPage -dCompatibilityLevel=1.4'
		os.popen('gs -o {0}-cropped.pdf {1} {0}-crop.pdf'.format(filename, gsParams))
	else:
		os.popen('cp {0}-crop.pdf {0}-cropped.pdf'.format(filename))
	
	# Return the new filename.
	pdfcropped = '{0}-cropped.pdf'.format(filename)
	
	print pdfcropped
	return pdfcropped
	
#---------------------------------------------------------------------------------------------------

def print_pdf(pdffile, landscape = False, fitplot = True):
	"""
	Print the local PDF file to the relevant printer.

	INPUTS
		pdffile: The file to be printed.

	OPTIONAL INPUTS
		landscape: Set this True to print the crossword in landscape (rotated 90 degrees).
		fitplot: Set this to have the printer scale the file to the paper size.
	"""
	
	printcmd = 'lp -n 2 '
	if fitplot == True:
		printcmd += '-o fitplot '
	if landscape == True:
		printcmd += '-o landscape '
	printcmd += '-d{0} {1}'.format(cw.printer, pdffile)

	os.popen(printcmd)
	return 1

#---------------------------------------------------------------------------------------------------

def delete_pdf(pdffile):
	"""
	Deletes the original PDF file and just keep the cropped one.

	INPUTS
		pdffile: The file to be deleted, alongside the associated -crop.pdf file.
	"""
	
	os.popen('rm {0}'.format(pdffile))
	os.popen('rm {0}-crop.pdf'.format(os.path.splitext(pdffile)[0]))
	return 1

#---------------------------------------------------------------------------------------------------

def today():
	"""
	Downloads and prints the (cropped) PDF of today's Quick Crossword.
	"""

	# Get the PDF, download it and crop it.
	pdfurl, _ = get_xword_url()
	pdffile = download_pdf(pdfurl)
	pdfcropped = crop_pdf(pdffile, pdfcrop = cw.pdfcrop, ghostscript = cw.ghostscript)

	# Print it, delete the extraneous bits.	
	printpdf = print_pdf(pdfcropped, fitplot = cw.fitplot)
	deletepdf = delete_pdf(pdffile)
	
#---------------------------------------------------------------------------------------------------

def saturday():
	"""
	Downloads and prints the (cropped) PDF of Saturday's Quick Crossword.
	"""
	
	# Get the PDF, download it and crop it.
	xwordno = get_saturday_xword_no()
	pdfurl, _ = get_xword_url(xwordno = xwordno)
	pdffile = download_pdf(pdfurl, saturday = True)
	pdfcropped = crop_pdf(pdffile, pdfcrop = cw.pdfcrop, ghostscript = cw.ghostscript)
	
	# Print it, delete the extraneous bits.
	if cw.ghostscript == True:
		landscape = False
	else:
		landscape = True

	printpdf = print_pdf(pdfcropped, landscape = landscape, fitplot = cw.fitplot)
	deletepdf = delete_pdf(pdffile)

#---------------------------------------------------------------------------------------------------

def archive(xwordno = 0):
	"""
	Downloads and prints the (cropped) PDF of an old Quick Crossword.

	OPTIONAL INPUTS
		xwordno: Set this to print a specific crossword number.
	"""

	# Get the next PDF, download it and crop it.
	if xwordno == 0: xwordno = next_xword_no(cw.username)
	pdfurl, actualxwordno = get_xword_url(xwordno = xwordno)
	pdffile = download_pdf(pdfurl, archive = actualxwordno)
	pdfcropped = crop_pdf(pdffile, pdfcrop = cw.pdfcrop, ghostscript = cw.ghostscript)

	# Work out whether the resulting file is landscape, set options accordingly.
	# If we use ghostscript, it'll set the file rotation to 90 automatically, so the landscape
	# keyword can be left alone; if not, use a crude method to determine landscapeness.
	if (cw.ghostscript == False) & ((int(xwordno) - 12394) % 6 == 0):
		landscape = True
	else:
		landscape = False
	
	# Print it, delete the extraneous bits.
	printpdf = print_pdf(pdfcropped, landscape = landscape, fitplot = cw.fitplot)
	deletepdf = delete_pdf(pdffile)

#---------------------------------------------------------------------------------------------------

# This stuff is at the bottom bceause it needs to run on import but after the functions have been
# defined so that the preferences function can be called.

config = ConfigParser.SafeConfigParser()
read = config.read(os.path.dirname(__file__) + '/preferences.cfg')

if read == []:
	# Ask the user to set up the preferences.
	printerName = raw_input('What is the name of the printer you will be using? ')
	username = raw_input('What is your username on this computer? ')
	cw.preferences(printerName, username)

# Read the values back out of the config file.
printer = config.get('Printer', 'Name')
username = config.get('Installation', 'Username')

try:
	fitplot = bool(config.get('Printer', 'fitplot'))
	ghostscript = bool(config.get('Dependencies', 'ghostscript'))
	pdfcrop = bool(config.get('Dependencies', 'pdfcrop'))
	PyPDF2 = bool(config.get('Dependencies', 'PyPDF2'))
except:
	cw.preferences(printer, username)