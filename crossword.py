#!/usr/bin/env python
# encoding: utf-8
"""
A module which, on import, yields functions for automatically printing the Guardian crossword.
Based on a Python script written by Jonny Nichols (University of Leicester) in the dim past.

Author:	John Coxon, Space Environment Physics group, University of Southampton
Date:	2015/02/27
"""

import datetime, inspect, os, urllib2, ConfigParser, crossword as cw

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

#---------------------------------------------------------------------------------------------------

def preferences(printerName, username, fitplot = True, ghostscript = True, pdfcrop = True, PyPDF2 = True):
	"""

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
	with open(os.path.dirname(__file__) + '/preferences.cfg', 'wb') as preferences:
		config.write(preferences)

	cw.fitplot = fitplot
	cw.ghostscript = ghostscript
	cw.pdfcrop = pdfcrop
	cw.PyPDF2 = PyPDF2
	cw.printer = printerName
	cw.username = username

#---------------------------------------------------------------------------------------------------

def get_saturday_xword_no():
	"""
	Gets the number of last Saturday's crossword based on specified epoch.
	Epoch tends to become 1 out around Christmastime, so needs to be updated annually.
	Current epoch definition: 13,974 occurred on 2015-02-21.
	"""
	
	# Get the current date and day of week.
	today = datetime.date.today()
	weekday = today.weekday()
	
	# Make delta T the number of days since last Saturday and subtract to get that date.
	difference = datetime.timedelta(weekday + 2)
	satdate = today - difference
	
	# Tell Python the epoch date.
	epoch = datetime.date(2015,2,21)
	
	# Get the difference between epoch and last Saturday, then calculate crossword number.
	epochdelta = satdate - epoch
	xwordno = ((epochdelta.days / 7.0) * 6.0) + 13974
	xwordno = int(xwordno)
	
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
	
	if xwordno != 0:
		url = 'http://www.theguardian.com/crosswords/quick/' + str(xwordno)
		print url
	else:
		url = 'http://www.theguardian.com/crossword/quick/'
	
	response = urllib2.urlopen(url)
	html = response.read()
	
	searchstr = '>PDF'
	loc = html.find(searchstr)
	urlstr = html[loc-80:loc]
	
	strsplit = urlstr.split('"')
	
	foundURL = False

	for substr in strsplit: 
		if substr[0] == 'h':
			pdfurl = substr
			foundURL = True
			break

	if (foundURL == False) & (xwordno != 0):
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
		landscape: Set this True to print the crossword in landscape.
	"""
	
	printcmd = 'lp -n 2 '
	if fitplot == True:
		printcmd += '-o fitplot '
	if landscape == True:
		printcmd += '-o landscape '
	printcmd += '-d{0} {1}'.format(crossword.printer, pdffile)
	
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
	pdfcropped = crop_pdf(pdffile)

	# Print it, delete the extraneous bits.	
	printpdf = print_pdf(pdfcropped)
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
	pdfcropped = crop_pdf(pdffile)
	
	# Print it, delete the extraneous bits.
	printpdf = print_pdf(pdfcropped, landscape = True)
	deletepdf = delete_pdf(pdffile)

#---------------------------------------------------------------------------------------------------

def archive(xwordno = 0):
	"""
	Downloads and prints the (cropped) PDF of an old Quick Crossword.

	OPTIONAL INPUTS
		xwordno: Set this to print a specific crossword number.
		PyPDF2: Set this to False to avoid the PyPDF2 dependency. This will mean that some
			crosswords are the wrong way around, regrettably, depending on epoch definition.
	"""

	# Get the next PDF, download it and crop it.
	if xwordno == 0: xwordno = next_xword_no(cw.username)
	pdfurl, actualxwordno = get_xword_url(xwordno = xwordno)
	pdffile = download_pdf(pdfurl, archive = actualxwordno)
	pdfcropped = crop_pdf(pdffile, pdfcrop = cw.pdfcrop, ghostscript = cw.ghostscript)

	# Work out whether the resulting file is landscape.
	if cw.PyPDF2 == True:
		import PyPDF2
		pdf = PyPDF2.PdfFileReader(pdfcropped)
		page = pdf.getPage(0)
		landscape = (('/Rotate', 90) in page.items())
	else:
		if (int(xwordno) - 12394) % 6 == 0:	
			landscape = True
		else:
			landscape = False
	
	# Print it, delete the extraneous bits.
	printpdf = print_pdf(pdfcropped, landscape = landscape, fitplot = cw.fitplot)
	deletepdf = delete_pdf(pdffile)