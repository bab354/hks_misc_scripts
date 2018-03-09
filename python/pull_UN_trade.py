'''

This script was used to access Data from the UN Comtrade Database
URL: https://comtrade.un.org

NOTE: Before running code below you have authenticate your IP by going to
link above
'''
import shutil
import urllib2
import zipfile
import os
import pandas as pd
import numpy as np

# PUT Destination folder where you want write data to
out_path = "C:/Users/blabarr/hks_misc_scripts"

def Download_UN_Data(data_type, freq, year, classification):
    '''Download data from UN CommTrade Bulk API and write to CSV in Dropbox folder
    
    Parameters:
        data_type (str) - 'C' (Commodities) or 'S' (Services)
        freq (str) -      'A' (Annual) or 'M' (Monthly)
               NOTE MONTHLY ONLY GOES BACK TO 2010
        year(str) -  2004 (Annually) or 200404 (Monthly) 4 string Year or 6 string yearmonth for Monthly
        classification (str) - Trade data classification scheme (see website)
            Briefly:    
            Harmonized System - 'H0' - 'H4'
            Standard International Trade Classification - 'S1' - 'S4'
            Broad Economic Categories - 'BEC'
            Extended Balance of Payments Services - 'EB02'
    '''
    assert(data_type in ['C', 'S'])
    assert(classification in ['HS', 'H0', 'H1', 'H2', 'H3', 'H4', 'S1', 'S2', 'S3', 'S4', 'BEC', 'EB02'])
    if freq == 'A':
        fold = "Annual"
    else:
        fold = 'Monthly'
    # Return Data in a Zip File
    url = 'http://comtrade.un.org/api/get/bulk/%s/%s/%s/ALL/%s' %(data_type, freq, year, classification)
    response = urllib2.urlopen(url)
    zip_name = r'%s\commtrade.zip' %out_path
    with open(zip_name, 'wb') as f:
        f.write(response.read())
    # Extract CSV from Zip and Delete Zip
    z = zipfile.ZipFile(zip_name)
    csv_name = z.namelist()[0]
    z.extractall(out_path)
    z.close()
    os.remove(zip_name)
    
if __name__ == '__main__':
    # Download Raw Files from Bulk API.
    # I want annual commodities in H1 Classification
    for year in range(2013, 2014):
       print("Pulling Data for Year: %i" %year)
       Download_UN_Data('C', 'A', year, 'H1')    