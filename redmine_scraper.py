from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import configparser

# function to initialize the driver and login
def login_to_redmine(driver, username, password):
    driver.get("https://redmine.kelsius.com/login")
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)  # press enter to login
    time.sleep(2)  # Wait for login to complete

# function to fetch the page content and return bs object
def get_page_content(driver, url):
    driver.get(url)
    time.sleep(0.1)
    return BeautifulSoup(driver.page_source, "html.parser")

# function to calculate whether the branch was closed greater than two weeks ago
def is_date_greater_than_two_weeks(date_str):
    input_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    two_weeks_ago = datetime.now() - timedelta(weeks=2)
    return input_date < two_weeks_ago

# function to extract matching data using regex pattern
def extract_matching_data(soup, pattern, output_file, write_mode):
    total_matches = 0
    branches = soup.select("tbody td.cf_8.string")
    dates = soup.select("tbody td.updated_on")

    with open(output_file, write_mode) as file:
        for i in range(len(branches)):
            branch_name = branches[i].get_text().strip()
            date = dates[i].get_text().strip()
            if re.match(pattern, branch_name) and is_date_greater_than_two_weeks(date):
                total_matches += 1
                file.write(branch_name + '\n')  # write the branch name to branches.txt

    return total_matches

# function to get the total number of pages from pagination
def get_last_page_number(soup):
    pages = soup.find_all("li", class_="page")
    return int(pages[-2].get_text()) if pages else 1

def load_credentials(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    username = config.get('login', 'username')
    password = config.get('login', 'password')
    
    return username, password

def main():
    # initialize the web driver
    driver = webdriver.Chrome()  # Ensure chromedriver is in your PATH

    username, password = load_credentials('config.ini')

    # loogin to redmine
    login_to_redmine(driver, username, password)

    # set up base URL and pattern
    base_url = "https://redmine.kelsius.com/projects/portal-manager/issues?c%5B%5D=tracker&c%5B%5D=status&c%5B%5D=priority&c%5B%5D=subject&c%5B%5D=assigned_to&c%5B%5D=updated_on&c%5B%5D=due_date&c%5B%5D=fixed_version&c%5B%5D=cf_8&f%5B%5D=status_id&f%5B%5D=tracker_id&f%5B%5D=&group_by=&op%5Bstatus_id%5D=c&op%5Btracker_id%5D=%3D&per_page=300&set_filter=1&sort=id%3Adesc&t%5B%5D=&utf8=%E2%9C%93&v%5Btracker_id%5D%5B%5D=1&page={}"
    pattern = r'[a-zA-Z]+-\d+-[a-zA-Z0-9-]+'

    output_file = "branches.txt"

    # start by scraping the first page
    soup = get_page_content(driver, base_url.format(1))
    total_branches = extract_matching_data(soup, pattern, output_file, 'w')

    # get the last page number and loop through all pages
    last_page = get_last_page_number(soup)
    for page_num in range(2, last_page + 1):
        soup = get_page_content(driver, base_url.format(page_num))
        total_branches += extract_matching_data(soup, pattern, output_file, 'a')

    # output total matches and close the browser
    print(f"Total matching branches: {total_branches}")
    driver.quit()

if __name__ == "__main__":
    main()
