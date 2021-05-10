  
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import time
from collections import deque
import requests
import sys
import datetime
import argparse
import concurrent.futures

# Setting up arguments for script
parser = argparse.ArgumentParser()

parser.add_argument("-s", "--site", dest="site", help="Website with http:// or https://", required=True)
parser.add_argument("-f", "--folder", dest="folder", help="Name of the folder this report is stored in.", required=True)
parser.add_argument("-c", "--crawl", dest="crawl", action='store_true', help="If you only want to crawl the site to verify all links are working.")
parser.add_argument("-i", "--ignore", dest="ignore", action='store_true', help="Add a list of sub domains (NOT external links) to exclude from the search. \nEach excluded url should be added on a new line in the 'exclude.txt' file. \nAll that's needed in this text file is the domain without the http/https protocols.")

args = parser.parse_args()

# Enable browser logging
caps = webdriver.DesiredCapabilities.CHROME.copy()
caps['perfLoggingPrefs'] = True

# Instantiate a chrome options object so you can set the size and headless preference
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-extensions") # Since it's headless, might not need it. Checking to see. 

# Change this if you want logs to show up in console
chrome_options.add_argument("log-level=3")
driver = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)

# Base url to check
base_url = args.site.rstrip("/")

# Variable for logs
logs = driver.get_log('browser')

# Using this to remove http from url
check_url = base_url.replace("http://", '').replace("https://", '')
check_url = check_url.split("/")[0]

# Check for additional domains to exclude
url_domain_check = check_url.split('.')
url_domain_name_check = url_domain_check[0]

# List for sub domain check with http/https appended to it
http_dncl = "http://"+url_domain_check[0]+"."
https_dncl = "https://"+url_domain_check[0]+"."

# Headers
headers_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}

# Urls to be checked
new_urls = deque([base_url])

# Urls we have already checked
processed_urls = set()

# Urls inside the scope of the domain
local_urls = set()

# Urls outside of the scope of the domain
foreign_urls = set()

# Logging requests for processed urls for validation. This logs to a separate file from the report.
req_log = set()

# Urls which reported errors
broken_urls = set()

# Urls with mailto or tel links
phone_mail_urls = set()

# Console logs set for each page
console_logs = set()

# Ignored URLs
ignore_urls = set()

# Create folder
os.mkdir(args.folder)

# Directory
directory = "./"+args.folder+"/"

# Report file
f = open(directory+args.folder+"-report.txt", "w+")

# Start time
st = datetime.datetime.now()

f.write("Started: " + st.strftime("%x") + " " + st.strftime("%I"+ ":" + "%M" + "%p"))

# Variable for excluded urls
ex_urls_file_path = "exclude.txt"
excluded_urls = open('exclude.txt', 'r')
updated_excluded_urls = set()

# If args.ignore is set
if args.ignore:

    # Parsing excluded URLs
    for e_url in excluded_urls:
        stripped_line = e_url.strip()
        new_line = stripped_line.replace("http://","").replace("https://","").rstrip('/')
        
        # Store updated exclusion links to memory
        updated_excluded_urls.append(new_line)

    excluded_urls.close


def get_links(elem):
    
    # Removing www. if this is in the href
    href = elem.get_attribute('href')
    href = href.replace("www.","")

    # Parsing href to help check links. Removes http://, https://, trailing slash, and everything after the first slash, and www if this exists.
    # This should only return the sub domain.
    # Example: subdomain.domain.tld
    parsed_href = href.strip()
    new_href_parsed = parsed_href.replace("http://","").replace("https://","").rstrip('/').split("/")[0].replace("www.","")

    if href is not None:

        # If ignore flag is True and the href is not in ignore URL
        if args.ignore and href not in ignore_urls: 

            # Check to see if href is in list of urls
            for ex_url in updated_excluded_urls:

                if ex_url in href:

                    # Append href to ignored URL
                    ignore_urls.add(href)

                # Breaking out of for loop
                break
                
        # Removing name anchor tags and urls on ignore list
        if "#" not in href and href not in ignore_urls:

            # If link has 'mailto' or 'tel', add href to temp_list
            if 'mailto:' in href or 'tel:' in href:

                # Gets stored on a temp list, then once all the links are checked on the page, this gets appended to the mailto/tel links for that page
                temp_list.append(href)

            # Checking links that do not have mailto / tel attributes
            elif "mailto" not in href and "tel" not in href:
                
                # Removes trailing forward slash, otherwise it treats this as new link
                href = href.rstrip("/")

                # Checking HTTP response for href
                try:
                    response = requests.session().get(href, headers=headers_dict)

                    if response.status_code != 999:

                        # logging response to add to req_log set
                        req_log.add(str(response.status_code) + ": " + href)

                except requests.exceptions.RequestException as e: 

                    # If url is broken, log the url, href and code
                    broken_urls.add("Found on " + url + "\n" + href + "\n" + "Error:" + "\n" + str(e) + "\n")
                    req_log.add(str(response.status_code) + ": " + href)
 
                
                # Checking to see if response code is not 200 or 999. Linkin really doesn't like robots crawling their site and they return a 999 error. 
                if response.status_code != 200 and response.status_code != 999:
                    broken_urls.add("Found on " + url + "\n" + str(response.status_code) + ": " + href + "\n")
                    req_log.add(str(response.status_code) + ": " + href)

                # Checks if url is within the same domain of the website, and checks to see if this has sub domains
                # Sub domains come up and we don't really want to worry about them if we don't control them. So these can be added to the list to ignore as you go.
                # First, we check to see if the check_url is in the href
                # check_url = domain.tld
                if check_url in href:
                
                    # Next, We need to see if new_href_parsed is in check_url. This should rule out regular local urls
                    # new_href_parsed = href without www, http://, https://, or trailing shashes at the end
                    if new_href_parsed in check_url:

                        # Add url to local_urls set
                        local_urls.add(href)

                        # Checks to see if url exists in new_url, and has not already been processed
                        if href not in new_urls and href not in processed_urls:
                            
                            # Adds to new urls to be processed
                            new_urls.append(href)

                    # This condition is trying to determine if this is a sub domain. We just need 1 more validation for sub domains.
                    # OR if (http://domain.) is in the href
                    # OR (https://domain.) is in the href
                    elif http_dncl in href or https_dncl in href:

                        # If href is not in updated excluded urls
                        if new_href_parsed not in updated_excluded_urls:

                            while True:

                                try:
                                    add_url_question = input('Similar URL found: '+href+'\n Do you want to add ' + href.split("/")[2] + ' to the ignore list? (y/n)')

                                except ValueError:
                                    print(f"Sorry, I did not under stand your input. Please try again instead of typing {add_url_question}")
                                    continue
                            
                                if add_url_question.lower() not in ('y','n'):
                                    print(f"Unfortunately {add_url_question} is not valid. The answer MUST be y or n")
                                    continue
                                else:
                                    break
                            
                            # If this URL needs to be added, add the parsed_excluded_urls to a list so we can continue to match based on this URL, and add the href to ignore_urls set.
                            if add_url_question == 'y':
                                question_url_adjustment = href.split('/')[2]
                                updated_excluded_urls.add(question_url_adjustment)
                                ignore_urls.add(href)

                        """ End Function """

                else:

                    # Adds to foreign urls list
                    foreign_urls.add(href)

with concurrent.futures.ThreadPoolExecutor() as executor:
    try:
        # If there's urls to be processed
        while len(new_urls):
            
            print(" Urls in queue: "+str(len(new_urls)), end="\r")

            # Links that have mailto or tel properties
            temp_list = []

            # Move next url from the queue to the set of processed urls
            url = new_urls.popleft()
            processed_urls.add(url)        

            # Going to URL with Selenium
            driver.get(url)

            # Added small timeout to make sure elements are loaded
            time.sleep(2)

            # Fetching all a tags
            elems = driver.find_elements_by_tag_name('a')

            # Looping through elements with concurrent futures threading
            with concurrent.futures.ThreadPoolExecutor() as ex:
                ex.map(get_links, elems)
                # href = elem.get_attribute('href')

            # If crawl only is not enabled
            if args.crawl is not True:
                # If there's errors in the console log
                for entry in driver.get_log('browser'):

                    # Storing level, message and source to variables
                    level = str(entry['level'])
                    message = str(entry['message'])

                    # Add logs to console_log set
                    console_logs.add("-Page: " + url + "\n" + "Category: " +  level + "\n" + "Error: " + message + "\n")
        
            # Checking to see if mailto and tel links exist for page, adding pages to phone_mail_urls
            if len(temp_list):
                u = '\n'.join(temp_list)

                phone_mail_urls.add("-Page: " + str(url) + "\n" + str(u) + "\n")

    except KeyboardInterrupt:
        sys.exit()

driver.quit()

# ~~~ Writing data sets to file

# Ignored links
if ignore_urls:
    f.write("\n")
    f.write("\nIgnored Links: " + str(len(ignore_urls)) + "\n")
    f.write('\n'.join(map(str, ignore_urls)))

# Local URLs
f.write("\n")
f.write("\nLocal Links: " + str(len(local_urls)) + "\n")
f.write('\n'.join(map(str, local_urls))) 

# Foreign Links
f.write("\n")
f.write("\nForeign Links: " + str(len(foreign_urls)) + "\n")
f.write('\n'.join(map(str, foreign_urls))) 

# Processed Links
f.write("\n")
f.write("\nProcessed Links: " + str(len(processed_urls)) + "\n")
f.write('\n'.join(map(str, processed_urls))) 

# Broken Links
f.write("\n")
f.write("\nBroken Links: " + str(len(broken_urls)) + "\n")

if len(broken_urls):
    f.write('\n'.join(map(str, broken_urls))) 
else:
    f.write("All URLs reported OK\n")

# Mailto and Tel links
f.write("\n")
f.write("\nMailto | Tel Links: " + "\n")
f.write('\n'.join(map(str, phone_mail_urls)))

# Console Logs
if args.crawl is True:
    f.write("\n")
    f.write("Console Logs: Crawl Only flag set, no console logs gathered.\n")
else:
    f.write("\n")
    f.write("Console Logs: " + str(len(console_logs)) + "\n")
    f.write('\n'.join(map(str, console_logs))) 

# Writing HTTP logs of all reqeusts
req_file = open(directory+args.folder+"-response-codes.txt", 'w+')
req_file.write("Site: " + check_url + "\n")
req_file.write('All HTTP Link Responses: ' + str(len(req_log)) + "\n")
req_file.write('\n'.join(map(str, req_log)))

f.write("\n")

# Finish time
fin = datetime.datetime.now()
f.write("\nEnded: " + fin.strftime("%x") + " " + fin.strftime("%I"+ ":" + "%M" + "%p"))

print("~~~ Link Checker Completed ~~~")

# Function to create CSV files from data set
def make_csv(filename, title_rows, set_name):
    download_dir = filename
    file = open(download_dir, 'w+')
    content = set_name
    content = [line.rstrip('\n') for line in content]
    columnTitleRow = title_rows
    file.write(columnTitleRow)

    # If there's no content, note in CSV
    if content == 0:
        file.write(columnTitleRow+"\n")
        file.write("Nothing to report")

    # Else, write it into the CSV line by line
    else: 
        for line in content:
            row = line+"\n"
            file.write(row)

    file.close()
