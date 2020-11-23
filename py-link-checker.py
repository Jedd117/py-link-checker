from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time
from collections import deque
import requests
import sys
import datetime

"""
This was created because most other methods do not render any javascript on the page,
meaning any JS that is used on the page will not be seen.  

Using Seleninm to crawl the site and get all of the links, and requests just for testing the url. 

Requirements:
download the chrome driver from https://sites.google.com/a/chromium.org/chromedriver/downloads 
and put it in the current directory 
"""

# Base url to check
base_url = sys.argv[1]

# Using this to remove http from url
check_url = base_url.replace("http://", '')
check_url = check_url.split("/")[0]

# Urls to be checked
new_urls = deque([base_url])

# Urls we have already checked
processed_urls = set()

# Urls inside the scope of the domain
local_urls = set()

# Urls outside of the scope of the domain
foreign_urls = set()

# Logging requests for processed urls for validation
req_log = set()

# Urls which reported errors
broken_urls = set()

# Urls with mailto or tel links
phone_mail_urls = set()

# Report file
f = open(check_url+"-report.txt", "w+")

t = datetime.datetime.now()

f.write("Started: " + t.strftime("%x") + " " + t.strftime("%I"+ ":" + "%M" + "%p"))

# instantiate a chrome options object so you can set the size and headless preference
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")

#Change this if you want logs to show up in console
chrome_options.add_argument("log-level=3")
chrome_driver = os.getcwd() +"\\chromedriver.exe"
driver = webdriver.Chrome(options=chrome_options, executable_path=chrome_driver)

try:
    while len(new_urls):

        # Links that have mailto or tel properties
        temp_list = []

        # Move next url from the queue to the set of processed urls
        url = new_urls.popleft()
        processed_urls.add(url)
        
        # Get url's content
        print("Processing %s" % url)

        # Testing to see if the url works with requests
        try:
            response = requests.get(url)

            # logging response to add to req_log set
            req_log.add(str(response.status_code) + ": " + url)

        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema):

            # If url is broken, add to broken urls
            broken_urls.add(response.status_code + ": " + url)
            continue 

        # Going to URL with Selenium
        driver.get(url)

        # Added sleep to prevent elements not loading in time. Set this to a higher number so make sure all JS is loaded.
        time.sleep(5)

        # Fetching all a tags
        elems = driver.find_elements_by_tag_name('a')

        # Fetching all tel tags
        for elem in elems:
            href = elem.get_attribute('href')
            if href is not None :

                # If link has 'mailto' or 'tel', add href to temp_list
                if 'mailto:' in href or 'tel:' in href:

                    temp_list.append(href)
                    # temp_list_page.append(url)

                # Checking links that do not have mailto / tel attributes
                elif "mailto" not in href and "tel" not in href:
                    
                    # Removes trailing forward slash, otherwise it treats this as new link
                    href = href.rstrip("/")

                    # Checking HTTP response for href
                    try:
                        response = requests.get(href)

                        # logging response to add to req_log set
                        req_log.add(str(response.status_code) + ": " + href)

                    # except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema):
                    except requests.exceptions.RequestException as e: 
                        print(e)
                        # If url is broken, log the url, href and code
                        broken_urls.add("Found on " + url + "\n" + str(response.status_code) + ": " + href + "\n" + "Error:" + "\n" + str(e) + "\n")
                        continue 

                # Checks if url is within the same domain of the website
                if check_url in href:

                    # Add url to local_urls set
                    local_urls.add(href)

                    # Checks to see if url exists in new_url, and has not already been processed
                    if href not in new_urls and href not in processed_urls:
                        
                        # Adds to new urls to be processed
                        new_urls.append(href)
                else:

                    # Adds to foreign urls list
                    foreign_urls.add(href)

        # Checking to see if mailto and tel links exist for page, adding pages to phone_mail_urls
        if len(temp_list):
            u = '\n'.join(temp_list)

            phone_mail_urls.add("-Page: " + str(url) + "\n" + str(u) + "\n")

except KeyboardInterrupt:
    sys.exit()

# Writing Data
f.write("\n")
f.write("\nLocal Links: " + str(len(local_urls)) + "\n")
f.write('\n'.join(map(str, local_urls))) 

f.write("\n")
f.write("\nForeign Links: " + str(len(foreign_urls)) + "\n")
f.write('\n'.join(map(str, foreign_urls))) 

f.write("\n")
f.write("\nProcessed Links: " + str(len(processed_urls)) + "\n")
f.write('\n'.join(map(str, processed_urls))) 

f.write("\n")
f.write("\nBroken Links: " + str(len(broken_urls)) + "\n")
if len(broken_urls):
    f.write('\n'.join(map(str, broken_urls))) 
else:
    f.write("All URLs reported OK\n")

f.write("\n")
f.write("\nMailto | Tel Links: " + "\n")
f.write('\n'.join(map(str, phone_mail_urls))) 

# Writing HTTP logs of all reqeusts
req_file = open(check_url + "-response-codes.txt", 'w+')
req_file.write("Site: " + check_url + "\n")
req_file.write('All HTTP Link Responses: ' + str(len(req_log)) + "\n")
req_file.write('\n'.join(map(str, req_log)))

f.write("\n")
f.write("\nEnded: " + t.strftime("%x") + " " + t.strftime("%I"+ ":" + "%M" + "%p"))
driver.quit()