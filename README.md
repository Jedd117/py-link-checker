# py-link-checker
This is a website crawler that will get all URLs on a website and tests them to make sure they're valid. Afterwards, this generates a report with a break down of all local / non-local urls, console log errors, tel/mailto links. These reports are saved in the folder you declare with the -f/--folder parameter.<br>

This script uses python and headless selenium. Selenium was used so dynamically generated JS content can be loaded.

This script is not as fast as something like scrapy, but it works.

## Prerequisites:
- Python 3
- Selenium Chrome Driver for your version of chrome installed on your machine
- Environment path setup for your chrome driver

### Make sure you have Python 3 installed. You can check by typing this in your terminal:
`python --version`

### Clone the repo:
`git clone REPO`

### Navigate to the directory:
`cd py-link-checker`

### Install Requirements:
`pip3 install -r requirements.txt`

### Download the chrome driver
- PC - from https://sites.google.com/a/chromium.org/chromedriver/downloads
- MAC - in your shell, run `brew install chromedriver` (assuming you have installed [homebrew](https://brew.sh/)).

### Add Chrome Driver to your Environment Path:
- No instructions since this can vary based on OS.

### Run:
`python ./py-link-checker.py -s http://website.com -f nameOfFolder`

You can use either of the notations (example: -f or --folder)
```
 -h, --help                     show this help message and exit
 -s SITE, --site SITE           Website with http:// or https://
 -f FOLDER, --folder FOLDER     Name of the folder this scan is stored in
 
 
 Optional:
 -i, --ignore                   Ignore sub domains listed in the 'exclude.txt' file
 -c, --crawl                    Use this if you only want to crawl the site and test links
 ```
