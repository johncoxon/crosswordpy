#!/usr/bin/env python
# encoding: utf-8
"""
A module which, on import, yields functions for automatically printing the Guardian crossword.
Based on a Python script written by Jonny Nichols (University of Leicester) in the distant past.

Author:    John Coxon, Space Environment Physics group, University of Southampton
Date:    2015/02/27
"""
from builtins                   import input
import datetime as dt
import os
import inspect
import subprocess
import crosswordpy as xw

# For 2to3 compatibility.
try:
    from urllib2 import urlopen, HTTPError
    from ConfigParser import SafeConfigParser
except ImportError:
    from urllib.request import urlopen, HTTPError
    from configparser import SafeConfigParser

#---------------------------------------------------------------------------------------------------

def preferences(printer, fitplot = True, ghostscript = True, pdfcrop = True,
    PyPDF2 = True):
    """
    Saves user preferences connected to dependencies + the name and features of the desired printer.
    """
    config = SafeConfigParser()

    # Set up the printer preferences.
    config.add_section('Printer')
    config.set('Printer', 'Name', printer)
    config.set('Printer', 'fitplot', str(fitplot))

    config.add_section('Dependencies')
    config.set('Dependencies', 'ghostscript', str(ghostscript))
    config.set('Dependencies', 'pdfcrop', str(pdfcrop))
    config.set('Dependencies', 'PyPDF2', str(PyPDF2))

    # Save the preferences back to a file.
    with open(os.path.dirname(__file__) + '/preferences.cfg', 'w') as preferences:
        config.write(preferences)

    xw.fitplot = fitplot
    xw.ghostscript = ghostscript
    xw.pdfcrop = pdfcrop
    xw.PyPDF2 = PyPDF2
    xw.printer = printer

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

def next_xword_no():
    """Get the next number needed for the crossword."""

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
        xw_html = response.read().decode('utf-8')
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

    html = response.read().decode('utf-8')

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
            pdf_url = substr
            foundURL = True
            break

    if foundURL == False:
        pdf_url, actualxwordno = get_xword_url(xwordno = xwordno + 1)
    else:
        actualxwordno = xwordno

    return pdf_url, actualxwordno

#---------------------------------------------------------------------------------------------------

def download_pdf(pdf_url, saturday = False, archive = False):
    """
    Download the PDF and save to a local file.

    INPUTS
        pdf_url: The URL to download from.

    OPTIONAL INPUTS
        saturday: Set this to download the Saturday crossword.
        archive: Set this to download an old crossword.
    """
    if saturday != False:
        filename = '/saturday.pdf'
    elif archive != False:
        filename = '/archive/' + str(archive) + '.pdf'
    else:
        filename = '/today.pdf'

    response = urlopen(pdf_url)
    pdf_file = os.path.dirname(inspect.getfile(inspect.currentframe())) + filename
    with open(pdf_file, 'wb') as local_file:
        local_file.write(response.read())

    return pdf_file

#---------------------------------------------------------------------------------------------------

def crop_pdf(pdf_file, pdfcrop = True, ghostscript = True):
    """
    Crop the local PDF file to remove the large margins, using pdfcrop and ghostscript.

    INPUTS
        pdf_file: The PDF file to be cropped.
    """

    # Get just the path and basename, not the extension.
    filename = os.path.splitext(pdf_file)[0]

    # Crop the pdf.
    if pdfcrop == True:
        status = subprocess.call('pdfcrop --margins 10 {0}'.format(pdf_file), shell = True)
    else:
        status = subprocess.call('cp {0} {1}-crop.pdf'.format(pdf_file, filename), shell = True)

    if ghostscript == True:
        gsParams = '-sDEVICE=pdfwrite -sPAPERSIZE=a4 -dPDFFitPage -dCompatibilityLevel=1.4'
        status = subprocess.call('gs -o {0}-cropped.pdf {1} {0}-crop.pdf'.format(filename,
                 gsParams), shell = True)
    else:
        status = subprocess.call('cp {0}-crop.pdf {0}-cropped.pdf'.format(filename), shell = True)

    # Return the new filename.
    pdf_cropped = '{0}-cropped.pdf'.format(filename)

    return pdf_cropped

#---------------------------------------------------------------------------------------------------

def rotate_pdf(pdf_file):
    """
    Check the PDF orientation and rotate if necessary.
    """

    if xw.pyPdf == True:
        from pyPdf import pdf

        read_pdf = pdf.PdfFileReader(file(pdf_file))

        dimensions = read_pdf.getPage(0).mediaBox

        if dimensions[2] > dimensions[3]:
            write_pdf = pdf.PdfFileWriter()
            write_pdf.addPage(read_pdf.getPage(0).rotate(rotateClockwise(90)))
            write_pdf.write(file(pdf_file, 'wb'))
            write_pdf.close()

        return 0

    else:
        return 1

#---------------------------------------------------------------------------------------------------

def print_pdf(pdf_file, landscape = False, fitplot = True):
    """
    Print the local PDF file to the relevant printer.

    INPUTS
        pdf_file: The file to be printed.

    OPTIONAL INPUTS
        landscape: Set this True to print the crossword in landscape (rotated 90 degrees).
        fitplot: Set this to have the printer scale the file to the paper size.
    """

    printcmd = 'lp -n 2 '
    if fitplot == True:
        printcmd += '-o fitplot '
    if landscape == True:
        printcmd += '-o landscape '
    printcmd += '-d{0} {1}'.format(xw.printer, pdf_file)

    return subprocess.call(printcmd, shell = True)

#---------------------------------------------------------------------------------------------------

def delete_pdf(pdf_file):
    """
    Deletes the original PDF file and just keep the cropped one.

    INPUTS
        pdf_file: The file to be deleted, alongside the associated -crop.pdf file.
    """

    status1 = subprocess.call('rm {0}'.format(pdf_file), shell = True)
    status2 = subprocess.call('rm {0}-crop.pdf'.format(os.path.splitext(pdf_file)[0]), shell = True)

    return status1, status2

#---------------------------------------------------------------------------------------------------

def today():
    """
    Downloads and prints the (cropped) PDF of today's Quick Crossword.
    """

    # Get the PDF, download it and crop it.
    pdf_url, _ = get_xword_url()
    pdf_file = download_pdf(pdf_url)
    pdf_cropped = crop_pdf(pdf_file, pdfcrop = xw.pdfcrop, ghostscript = xw.ghostscript)

    # Print it, delete the extraneous bits.
    print_pdf(pdf_cropped, fitplot = xw.fitplot)
    delete_pdf(pdf_file)

#---------------------------------------------------------------------------------------------------

def saturday():
    """
    Downloads and prints the (cropped) PDF of Saturday's Quick Crossword.
    """

    # Get the PDF, download it and crop it.
    xwordno = get_saturday_xword_no()
    pdf_url, _ = get_xword_url(xwordno = xwordno)
    pdf_file = download_pdf(pdf_url, saturday = True)
    pdf_cropped = crop_pdf(pdf_file, pdfcrop = xw.pdfcrop, ghostscript = xw.ghostscript)

    # Print it, delete the extraneous bits.
    if xw.ghostscript == True:
        landscape = False
    else:
        landscape = True

    print_pdf(pdf_cropped, landscape = landscape, fitplot = xw.fitplot)
    delete_pdf(pdf_file)

#---------------------------------------------------------------------------------------------------

def archive(xwordno = 0):
    """
    Downloads and prints the (cropped) PDF of an old Quick Crossword.

    OPTIONAL INPUTS
        xwordno: Set this to print a specific crossword number.
    """

    # Get the next PDF, download it and crop it.
    if xwordno == 0: xwordno = next_xword_no()
    pdf_url, actualxwordno = get_xword_url(xwordno = xwordno)
    pdf_file = download_pdf(pdf_url, archive = actualxwordno)
    pdf_cropped = crop_pdf(pdf_file, pdfcrop = xw.pdfcrop, ghostscript = xw.ghostscript)

    # Work out whether the resulting file is landscape, set options accordingly.
    # If we use ghostscript, it'll set the file rotation to 90 automatically, so the landscape
    # keyword can be left alone; if not, use a crude method to determine landscapeness.
    if (xw.ghostscript == False) & ((int(xwordno) - 12394) % 6 == 0):
        landscape = True
    else:
        landscape = False

    # Print it, delete the extraneous bits.
    print_pdf(pdf_cropped, landscape = landscape, fitplot = xw.fitplot)
    delete_pdf(pdf_file)

#---------------------------------------------------------------------------------------------------

def run():
    config = SafeConfigParser()
    read = config.read(os.path.dirname(__file__) + '/preferences.cfg')

    try:
        # Read the values back out of the config file.
        xw.printer = config.get('Printer', 'Name')
    except:
        # Ask the user to set up the preferences.
        xw.printer = input('What is the name of the printer you will be using? ')

    try:
        xw.fitplot = bool(config.get('Printer', 'fitplot'))
        xw.ghostscript = bool(config.get('Dependencies', 'ghostscript'))
        xw.pdfcrop = bool(config.get('Dependencies', 'pdfcrop'))
        xw.PyPDF2 = bool(config.get('Dependencies', 'PyPDF2'))
    except:
        xw.preferences(printer)

run()
