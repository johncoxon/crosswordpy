"""
crossword

A module which, on import, yields functions for automatically printing the Guardian crossword.
Based on a Python script written by Jonny Nichols (University of Leicester) in the dim past.

Author:	John Coxon, Space Environment Physics group, University of Southampton
Date:	2015/02/27
"""

#!/usr/bin/env python
# encoding: utf-8

import datetime, inspect, os, urllib2

def get_saturday_xword_no():
	# Gets the number of last Saturday's crossword based on specified epoch.
	# Epoch tends to become 1 out around Christmastime, so needs updated annually.
	# Current epoch definition: 13,974 occurred on 2015-02-21.
	
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

	# Get the list of files from the archive directory and sort them.
	files = os.listdir(os.path.dirname(inspect.getfile(inspect.currentframe())) + '/archive')
	files.sort()
	
	# Get the number of files and then select the last file in the list.
	xwordno = files[-1]
	
	# Get the start of the filename and add 1 to get the next crossword desired.
	xwordno = int(xwordno[:5]) + 1
	
	return xwordno

#---------------------------------------------------------------------------------------------------

def get_xword_html(xwordno = 0):
	# Gets the Quick Crossword HTML from URL (from the crossword number if specified).
	
	if xwordno != 0:
		url = 'http://www.theguardian.com/crosswords/quick/' + str(xwordno)
		print url
	else:
		url = 'http://www.theguardian.com/crossword/quick/'
	
	response = urllib2.urlopen(url)
	html = response.read()
	
	return html	

#---------------------------------------------------------------------------------------------------

def extract_pdf_url(html):
	# Get the URL for the PDF from the HTML input.
	
	searchstr = '>PDF'
	loc = html.find(searchstr)
	urlstr = html[loc-80:loc]
	
	strsplit = urlstr.split('"')
	
	for substr in strsplit: 
		
		if substr[0] == 'h':
			pdfurl = substr
			break

	return pdfurl

#---------------------------------------------------------------------------------------------------

def download_pdf(pdfurl, saturday = False, archive = False):
	# Download the PDF and save to a local file.
	
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
	
def crop_pdf(pdffile):
	# Crop the local PDF file to remove the large margins.
	
	os.popen('pdfcrop --margins 10 ' + pdffile)
	os.popen('gs -o ' + os.path.splitext(pdffile)[0] + '-cropped.pdf -sDEVICE=pdfwrite -sPAPERSIZE=a4 -dFIXEDMEDIA -dPDFFitPage -dCompatibilityLevel=1.4 ' + os.path.splitext(pdffile)[0] + '-crop.pdf')
	
	pdfcropped = os.path.splitext(pdffile)[0] + '-cropped.pdf'
	
	print pdfcropped
	return pdfcropped
	
#---------------------------------------------------------------------------------------------------

def print_pdf(pdffile, landscape = False):
	# Print the local PDF file to the relevant printer.
	
	printcmd = 'lp -n 2 '
	if landscape == True: printcmd = printcmd + '-o landscape '
	printcmd = printcmd + '-dBlack_and_White_on_staff_printing_soton_ac_uk ' + pdffile
	os.popen(printcmd)
	return 1

#---------------------------------------------------------------------------------------------------

def delete_pdf(pdffile):
	# Delete the original PDF file and just keep the cropped one.
	
	os.popen('rm ' + pdffile)
	os.popen('rm ' + os.path.splitext(pdffile)[0] + '-crop.pdf')
	return 1

#---------------------------------------------------------------------------------------------------

def today():
	# Downloads and prints the (cropped) PDF of today's Quick Crossword.
	
	xwordhtml = get_xword_html()
	pdfurl = extract_pdf_url(xwordhtml)
	pdffile = download_pdf(pdfurl)
	pdfcropped = crop_pdf(pdffile)
	printpdf = print_pdf(pdfcropped)
	deletepdf = delete_pdf(pdffile)
	
#---------------------------------------------------------------------------------------------------

def saturday():
	# Downloads and prints the (cropped) PDF of Saturday's Quick Crossword.
		
	xwordno = get_saturday_xword_no()
	xwordhtml = get_xword_html(xwordno = xwordno)
	pdfurl = extract_pdf_url(xwordhtml)
	pdffile = download_pdf(pdfurl, saturday = True)
	pdfcropped = crop_pdf(pdffile)
	printpdf = print_pdf(pdfcropped, landscape = True)
	deletepdf = delete_pdf(pdffile)

#---------------------------------------------------------------------------------------------------

def archive(xwordno = 0):
	# Downloads and prints the (cropped) PDF of an old Quick Crossword.
	
	if xwordno == 0: xwordno = next_xword_no('jc3e14')
	xwordhtml = get_xword_html(xwordno = xwordno)
	pdfurl = extract_pdf_url(xwordhtml)
	pdffile = download_pdf(pdfurl, archive = xwordno)
	pdfcropped = crop_pdf(pdffile)
	if (int(xwordno) - 12394) % 6 == 0:
		printpdf = print_pdf(pdfcropped, landscape = True)
	else:
		printpdf = print_pdf(pdfcropped)
	deletepdf = delete_pdf(pdffile)