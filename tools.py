################################################################################
#          __  __ _              _ _                                           #
#         |  \/  (_)___  ___ ___| | | __ _ _ __   ___  ___  _   _ ___          #
#         | |\/| | / __|/ __/ _ \ | |/ _` | '_ \ / _ \/ _ \| | | / __|         #
#         | |  | | \__ \ (_|  __/ | | (_| | | | |  __/ (_) | |_| \__ \         #
#         |_|  |_|_|___/\___\___|_|_|\__,_|_| |_|\___|\___/ \__,_|___/         #
#                        |_   _|__   ___ | |___                                #
#                          | |/ _ \ / _ \| / __|                               #
#                          | | (_) | (_) | \__ \                               #
#                          |_|\___/ \___/|_|___/                               #
#                                                                              #
#           == A set of miscellaneous helper functions and tools ==            #
#                                                                              #
################################################################################
#                                                                              #
# [+] Written by:                                                              #
#  |_ Luis Martin (lumarti2@cisco.com)                                         #
#  |_ CITT Software CoE.                                                       #
#  |_ Cisco Advanced Services, EMEAR.                                          #
#                                                                              #
################################################################################
#                                                                              #
# Copyright (c) 2015-2016 Cisco Systems                                        #
# All Rights Reserved.                                                         #
#                                                                              #
#    Unless required by applicable law or agreed to in writing, this software  #
#    is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF   #
#    ANY KIND, either express or implied.                                      #
#                                                                              #
################################################################################

# Standard library imports
import sys

# External imports
import xlrd

# Globals
g_do_debug=False

# FUNCTION DEFINITIONS
def fatal(msg):
    """
    Prints and error message and aborts program execution
    """
    sys.stderr.write(msg+"\n")
    sys.exit(1)
    
def warning(msg):
    """
    Prints a warning message to stderr
    """
    sys.stderr.write(msg+"\n")

def output(msg):
    """
    Prints a message to stdout
    """
    sys.stdout.write(msg+"\n")

def debug(msg):
    """
    Prints a message to stdout only if the global g_do_debug var is True
    """
    global g_do_debug
    if g_do_debug==True:
        sys.stdout.write(msg+"\n")

def debug_enable():
    """
    Enables debug mode
    """
    global g_do_debug
    g_do_debug=True

def is_number(s):
    """
    Checks whether the supplied parameter is a number.
    @return True if the paremeter is a number.
    @return False if the parameter is not a number.
    """
    try:
        float(s)
        return True
    except ValueError:
        return False

def list_to_dict_by_key(slist, key):
    """
    This function takes a list of objects and returns a dictionary, indexed
    by the value of the supplied attribute
    @param slist is the list to convert
    @param key is the name of the object attribute to be used as key
    @return dictionary of objects in slist, indexed by key
    """
    mydict={}
    for l in slist:
        mydict[ l.__dict__[key] ] = l


def list_to_dict_by_method(slist, method):
    """
    This function takes a list of objects and returns a dictionary, indexed
    by the value returned by the supplied method
    @param slist is the list to convert
    @param method is the methor reference to be used as key
    @return dictionary of objects in slist, indexed by key
    """
    mydict={}
    for l in slist:
        mydict[ l.method() ] = l


def parse_spreadsheet(filename):
    """
    This function parses the supplied spreadsheet file. It iterates over all
    sheets. It returns a dictionary with one entry per sheet (key is the sheet name).
    Each entry contains a list of rows. Each row is itself a dictionary where
    cell values can be accessed using the relevant keys. Such keys are extracted
    from the top row of each sheet.

    Example:
    We have an excel with two sheets: "TENANTS" and "USERS"

     TENANTS:                           USERS
       +------+-------------+           +----------+----------+--------+
       | name | description |           | username | password | expire |
       +------+-------------+           +----------+----------+--------+
       | luis | Luis Tenant |           | lumarti2 | cisco123 | 2017   |
       | aitor| Aitor Tenant|           +------------------------------+
       +--------------------+
    
    The return data structure will look like this:
    result={'TENANTS' : [
                           {"name" : "luis", 'description': 'Luis Tenant'},
                           {"name" : "aitor", 'description': 'Aitor Tenant'}
                        ],
            'USERS' :   [
                           {'username': 'lumarti2', 'password' : 'cisco123' , 'expire': '2017'}
                        ]
            }

    @param filename is the name of the Excel spreadsheet to be parsed
    @warning Note that any numbers in cells of the spreadsheet will be converted to
             plain strings. Also, floats will be converted to integers, so don't
             expect the results to contain any decimal parts.
    @warning In tables containing column "##IGNORE##", rows with value "Yes" on
             such column, will be skipped.
    """
    contents={}

    # Open the source spreadsheet
    workbook=xlrd.open_workbook(filename=filename)

    # Iterate through the list of tabs (sheets)
    for tab in range(0, workbook.nsheets):

        # Fetch the current sheet
        worksheet = workbook.sheet_by_index(tab)
        tab_label = worksheet.name

        # For the first row, extract the column labes
        labels=[]
        for i in range(0, worksheet.ncols):
            labels.append(worksheet.row(0)[i].value)

        # Check whether the current table has an ignore field, so we can
        # later skip some lines
        if '##IGNORE##' in labels:
            do_ignore=True
        else:
            do_ignore=False

        entries=[]

        for i in range(1, worksheet.nrows):
            # Fetch row
            row = worksheet.row(i)
            entry={}
            # Store values on each cell
            for j in range(0, worksheet.ncols):

                # If it's a number, convert it to an integer first
                # (we don't want to end up reading eth/1.0/11.0)
                if is_number(row[j].value):
                    entry[ labels[j] ] = str( int(row[j].value) )
                else:
                    entry[ labels[j] ] = str(row[j].value)

            if do_ignore is False:
                entries.append(entry)
            elif do_ignore is True and entry['##IGNORE##'].lower()=="no":
                entries.append(entry)
            else:
                pass
                # output.debug("Ignored line %i" % i)

        # Store the data of this sheet
        contents[tab_label]=entries

    return contents
