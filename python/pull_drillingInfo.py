"""
The script pulls data from DrillingInfo's API. It was written by Blake Barr
in 2018 while working as a research assistant in Environmental Economics
for Professor Joe Aldy

This script does not contain data for all API datasets but it does provide code for most.

NOTE: I have commented out the API Key. This is easy to find on the website if you
have a DrillingInfo Account. These data are not publicy available. This script is simply meant
to assist those who have an account with acquiring the data
"""
import requests
import json
import csv
import os
import codecs
import pandas as pd

#DrillingInfo provides two different versions of data. Version 1 and Version 2
v2_datasets = ["well-origins", "wellbores", "completions", "completion-events",
               "producing-entities", "producing-entity-stats", "producing-entity-details" ]

v1_datasets = ["legal-leases", "landtrac-leases", "permits" , 'rigs', 'producing-entities-details', 'producing-entities']

drill_website = "https://di-api.drillinginfo.com"
v2_website = "%s/v2/direct-access" %drill_website
# INSERT DESTINATION WHERE YOU WANT TO WRITE FILES
dest =  ''

# NOTE: YOU CAN FIND THIS WHEN YOU LOG IN TO YOUR DRILLINGINFO ACCOUNT
API_key = ''
'''
NOTE: To Acquire V2 Data, you also needed a BearerToken. To acquire a Bearer token clients will need to
    base64 encode two values for client_id and client_secret together with a colon separating them.
    The base64 encoded result is then used in the Authorization header with scheme Basic.
    You will find your client_id and client_secret in same location as API_key
    
    I used the following website for Base 64 encoding:www.base64encode.org
    
    Example (Fake client_id and client_secret)
    client_id = abc
    client_secret = 123
    Use website to base_encode abc:123 and get 'sdfg4424'
    Authorization would be 'Basic sdfg4424'
'''
Authorization = 'Basic INSERT BASE ENCODED'


def AcquireBearerToken():
    """ This function returns a bearer token that will be used to acquire V2 Data
        ClientID and Client Secret needed to be base64 encoded with colon between them
        input: 15360-direct-access:30ae90c5-5f98-49dd-a4ed-10c3049e04cf
        website: www.base64encode.org """
    
    heads = {'X-API-KEY': API_key,
             'Content-Type' : 'application/x-www-form-urlencoded',
             'Authorization': Authorization,
             }
    r = requests.request("POST", "%s/tokens" %v2_website, data="grant_type=client_credentials", headers=heads)
    return(r.json().get('access_token'))


def Write_JSON_to_CSV(file_name, list_of_dict):
    """ Write rows of file_name using a list of dictionaries
        where each dicionary entry corresponds to a row of data where keys
        are variable names and values are the actual data
        
        Parameters:
        file_name (str) - file to write on
        list_of_dict (list) - list of dictionaries where each dict is a row of data
    """
    with open(file_name, "ab") as f:
        csvwriter = csv.writer(f)
        for i in range(len(list_of_dict)):
            try:
                csvwriter.writerow(list_of_dict[i].values())
            except:
                continue
         
def Make_API_Request(version_num, url, BearerToken = ""):
    """ Make a request call to DrillingInfo API
        Parameters:
            version_num (int) - version of data on DrillingInfo Website (1 or 2)
            url (str) - url of request
            BearerToken (str) - Token needed for v2 data
            
        Returns request object from API
    """
    if version_num == 1:
        heads = {'X-API-KEY': API_key, 'cache-control': "no-cache"}
    else:
        heads = {'X-API-KEY': API_key,
                 'cache-control': "no-cache",
                 'Authorization': BearerToken,
                 'Accept': "text/csv"}
    
    return(requests.request("GET",
                            "%s" %url,
                            headers=heads))

def Acquire_V1_data(drilling_var):
    """
    
        This function pulls Version 1 data from DrillingInfo website. These variables
        are only available in JSON Format. Furthermore, unlike V2 variables, there are no
        links to go through. Instead, you query the DrillingInfo Website for how many records
        there are for the given variable. Then you loop through pages until you get all records.
        The max is 100,000 records per page,
        but currently set it to 50,000 since I was getting memory error
        
        Parameters:
            drilling_var (str) - V1 drilling data-set name
    """
    assert(drilling_var in v1_datasets)
    headers = {'X-API-KEY': API_key, 'cache-control': "no-cache"}
    # Submit Head Request to get number of pages
    head_url = "%s/v1/direct-access/%s" %(drill_website, drilling_var)
    head = requests.request("HEAD","%s" %head_url, headers= headers)
    file_name = "%s/v1_%s.csv" %(dest, drilling_var)
        
    print(head.status_code)
    record_count = int(head.headers['X-QUERY-RECORD-COUNT'])
    if record_count == 0:
        return
    else:
        # Determine Number page pages = Records / pagesize + 1 (15.9 -> 16)
        pagesize = 50000
        num_pages = record_count / pagesize + 1
        for p in range(1, num_pages + 1):
            print(p)
            url = "%s?format=json&page=%i&pagesize=%i" %(head_url, p, pagesize)
            response = Make_API_Request(1, url)
            data_set = json.loads(response.text)
            # First Page need to write file and create var names
            if p == 1:   
                with open(file_name, "wb") as f:
                    csv.writer(f).writerow(data_set[0].keys())
            Write_JSON_to_CSV(file_name, data_set)
            
def change_CSV_encoding(file_name, data, append=False):
    """ This is a helper function used for Acquire_V2_drilling_data
    
    The response data is in CSV format so this function open a file
    and writes the data to the file_name. To prevent errors, this
    code uses utf8 format as some data could not be picked up by
    Python standard file opening
    
    Parameters
        file_name (str) - name of file to write data
        data (str) -  data in CSV format from DrillingInfo API
        append(bool) - appends to file if true
    """
    if append:
        action = 'ab'
    else:
        action = 'wb'
    f = codecs.open(file_name, action, encoding='utf8')
    f.write(data)
    f.close()
    
def Acquire_V2_Data(drilling_var, BearerToken):
    """
    This function pulls Version 2 data-sets from DrillingInfo API
    
    For V2, their data does not return pages to loop through. Instead, each request object
    contains links to the next page of results. However, the links do not end. Instead the last
    page of data just links to itself, so I use a while loop that stops when it sees a repeat link.
    
    Parameters:
        drilling_var (str) - one of the names of V2 datasets
        BearerToken (str) - BearerToken needed to access V2 data-sets
    """
    assert(drilling_var in v2_datasets)
    response = Make_API_Request(2,
                                "%s/%s?pagesize=%i" %(v2_website, drilling_var, 10000),
                                BearerToken)
    
    # To prevent unicode errors, changing encoding for CSV
    # that I write to
    file_name = "%s/v2_%s.csv" %(dest, drilling_var)
    change_CSV_encoding(file_name, response.text)
    
    # Links go on forever. Keep going until you see repeat link
    # since last link linkns to itself
    current_link = "stub"
    get_next_link = lambda x: requests.utils.parse_header_links(x["Links"])[1]['url']
    next_link = get_next_link(response.headers)
    while next_link != current_link:
        response = Make_API_Request(2, "%s%s" %(v2_website, next_link), BearerToken)
        # Write to File
        change_CSV_encoding(file_name, response.text, append=True)
        current_link = next_link
        next_link = get_next_link(response.headers)
    

if __name__ == '__main__':
    bearer = 'Bearer %s' %AcquireBearerToken()
    # ACQUIRE V1 DATA-SETS
    for v in v1_datasets:
        print("Pulling Data for: %s" %v)
        Acquire_V1_data(v)    
    # ACQUIRE V2 DATA-SET
    for v in v2_datasets:
        print("Pulling data for: %s" %v)
        Acquire_V2_Data(v, BearerToken=bearer)    
