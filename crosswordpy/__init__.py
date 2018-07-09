#!/usr/bin/env python
# encoding: utf-8
"""
A module which, on import, yields functions for automatically printing the Guardian crossword.
Based on a Python script written by Jonny Nichols (University of Leicester) in the distant past.

Author:	John Coxon, Space Environment Physics group, University of Southampton
Date:	2015/02/27
"""

import datetime as dt
import os
import inspect
import crosswordpy as xw

# For 2to3 compatibility.
try:
	from urllib2 import urlopen, HTTPError
	from ConfigParser import SafeConfigParser
except ImportError:
	from urllib.request import urlopen, HTTPError
	from configparser import SafeConfigParser

#---------------------------------------------------------------------------------------------------

def preferences(printer_name, username, fitplot = True, ghostscript = True, pdfcrop = True,
	PyPDF2 = True):
	"""
	Saves user preferences connected to dependencies, the name and features of the desired printer,
	and the username of the user (for use in recording crossword progress).
	"""
	config = SafeConfigParser()

	# Set up the printer preferences.
	config.add_section('Printer')
	config.set('Printer', 'Name', printer_name)
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

	xw.fitplot = fitplot
	xw.ghostscript = ghostscript
	xw.pdfcrop = pdfcrop
	xw.PyPDF2 = PyPDF2
	xw.printer = printer_name
	xw.username = username

#---------------------------------------------------------------------------------------------------

def get_saturday_xword_no():
	"""
	Gets the number of last Saturday's crossword by getting today's number and subtracting.
	Takes account of situations in which Christmas Day will screw up the mathematics.
	"""

	# Get the current date and day of week.
	today = dt.date.today()
	weekday = today.weekday()

	# Get the date on Saturday.
	saturday = today - dt.timedelta(weekday + 2)

	# Get today's crossword number.
	_, todayxwordno = get_xword_url()

	# Get Christmas Day as a dt object.
	xmas = dt.date(saturday.year, 12, 25)

	# Subtract to get Saturday's crossword number.
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
		xw_url = 'https://www.theguardian.com/crosswords/'
		try:
			response = urlopen(xw_url)
		except HTTPError:
			print('Error when accessing: ' + xw_url)
			raise
		xw_html = response.read()
		xw_search = 'https://www.theguardian.com/crosswords/quick/'
		xw_loc = xw_html.find(xw_search) + len(xw_search)
		if xw_loc != -1:
			xwordno = int(xw_html[xw_loc:xw_loc+5])
			actualxwordno = xwordno

	url = 'https://www.theguardian.com/crosswords/quick/' + str(xwordno)
	print(url)

	try:
		response = urlopen(url)
	except HTTPError:
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

	response = urlopen(pdfurl)
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

	if ghostscript == True:
		gsParams = '-sDEVICE=pdfwrite -sPAPERSIZE=a4 -dPDFFitPage -dCompatibilityLevel=1.4'
		os.popen('gs -o {0}-cropped.pdf {1} {0}-crop.pdf'.format(filename, gsParams))
	else:
		os.popen('cp {0}-crop.pdf {0}-cropped.pdf'.format(filename))

	# Return the new filename.
	pdfcropped = '{0}-cropped.pdf'.format(filename)

	print(pdfcropped)
	return pdfcropped

#---------------------------------------------------------------------------------------------------

def rotate_pdf(pdffile):
	"""
	Check the PDF orientation and rotate if necessary.
	"""

	if xw.pyPdf == True:
		from pyPdf import pdf

		read_pdf = pdf.PdfFileReader(file(pdffile))

		dimensions = read_pdf.getPage(0).mediaBox

		if dimensions[2] > dimensions[3]:
			write_pdf = pdf.PdfFileWriter()
			write_pdf.addPage(read_pdf.getPage(0).rotate(rotateClockwise(90)))
			write_pdf.write(file(pdffile, 'wb'))
			write_pdf.close()

		return 0

	else:
		return 1

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
	printcmd += '-d{0} {1}'.format(xw.printer, pdffile)

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
	pdfcropped = crop_pdf(pdffile, pdfcrop = xw.pdfcrop, ghostscript = xw.ghostscript)

	# Print it, delete the extraneous bits.
	printpdf = print_pdf(pdfcropped, fitplot = xw.fitplot)
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
	pdfcropped = crop_pdf(pdffile, pdfcrop = xw.pdfcrop, ghostscript = xw.ghostscript)

	# Print it, delete the extraneous bits.
	if xw.ghostscript == True:
		landscape = False
	else:
		landscape = True

	printpdf = print_pdf(pdfcropped, landscape = landscape, fitplot = xw.fitplot)
	deletepdf = delete_pdf(pdffile)

#---------------------------------------------------------------------------------------------------

def archive(xwordno = 0):
	"""
	Downloads and prints the (cropped) PDF of an old Quick Crossword.

	OPTIONAL INPUTS
		xwordno: Set this to print a specific crossword number.
	"""

	# Get the next PDF, download it and crop it.
	if xwordno == 0: xwordno = next_xword_no(xw.username)
	pdfurl, actualxwordno = get_xword_url(xwordno = xwordno)
	pdffile = download_pdf(pdfurl, archive = actualxwordno)
	pdfcropped = crop_pdf(pdffile, pdfcrop = xw.pdfcrop, ghostscript = xw.ghostscript)

	# Work out whether the resulting file is landscape, set options accordingly.
	# If we use ghostscript, it'll set the file rotation to 90 automatically, so the landscape
	# keyword can be left alone; if not, use a crude method to determine landscapeness.
	if (xw.ghostscript == False) & ((int(xwordno) - 12394) % 6 == 0):
		landscape = True
	else:
		landscape = False

	# Print it, delete the extraneous bits.
	printpdf = print_pdf(pdfcropped, landscape = landscape, fitplot = xw.fitplot)
	deletepdf = delete_pdf(pdffile)

#---------------------------------------------------------------------------------------------------


def run():
	# This stuff is at the bottom bceause it needs to run on import but after the functions have been
	# defined so that the preferences function can be called.

	config = SafeConfigParser()
	read = config.read(os.path.dirname(__file__) + '/preferences.cfg')

	if read == []:
		# Ask the user to set up the preferences.
		printer_name = raw_input('What is the name of the printer you will be using? ')
		username = raw_input('What is your username on this computer? ')
		xw.preferences(printer_name, username)
	else:

		# Read the values back out of the config file.
		printer = config.get('Printer', 'Name')
		username = config.get('Installation', 'Username')

		try:
			fitplot = bool(config.get('Printer', 'fitplot'))
			ghostscript = bool(config.get('Dependencies', 'ghostscript'))
			pdfcrop = bool(config.get('Dependencies', 'pdfcrop'))
			PyPDF2 = bool(config.get('Dependencies', 'PyPDF2'))
		except:
			xw.preferences(printer, username)
	pass

if __name__ == "__main__":
	run()
else:
	pass
