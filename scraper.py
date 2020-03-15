from selenium import webdriver
from bs4 import BeautifulSoup
import re
import os
from time import sleep
import json
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver")
SOURCE_DIR = './source'

class SalesScraper:

  def __init__(self, username, password, companyNames, fields):
    self.driver = None
    self.username = username
    self.password = password
    self.companyNames = companyNames
    self.fields = fields
    self.data = {}
    self.sourceDir = SOURCE_DIR
  
  def login(self):
    if self.driver:
      return

    self.driver = webdriver.Chrome(executable_path=DRIVER_BIN)
    self.driver.get('https://www.linkedin.com/login')
    username = self.driver.find_element_by_id('username')
    username.send_keys(self.username)
    sleep(0.5)
    password = self.driver.find_element_by_id('password')
    password.send_keys(self.password)
    sleep(0.5)
    log_in_button = self.driver.find_element_by_xpath('//*[@type="submit"]')
    log_in_button.click()
    sleep(1)
    

  def logout(self):
    if self.driver:
      self.driver.quit()

  def savePages(self, overwrite=True):
    existsSourceDir = os.path.exists(self.sourceDir)
    if existsSourceDir and not overwrite:
      return

    self.login()
    if not existsSourceDir:
      os.mkdir(self.sourceDir)
    for companyName in self.companyNames:
      page_source = self._getPageSource(companyName)
      soup = BeautifulSoup(page_source, 'html.parser')
      with open(os.path.join(self.sourceDir, f'{companyName}.html'), 'w') as file:
        file.write(soup.prettify())
    self.logout()


  def _getPageSource(self, companyName):
    if self.driver == None:
      return open(os.path.join(self.sourceDir, f'{companyName}.html'), 'r').read()
    
    self.driver.get(f'https://www.linkedin.com/company/{companyName}/about/')
    return self.driver.page_source

  def _scrapData(self, companyName):
    data = { }
    page_source = self._getPageSource(companyName)
    soup = BeautifulSoup(page_source, 'html.parser')
    
    for f in self.fields:
      pattern = re.compile(rf'{f}')
      data[f] = soup.find('dt', text=pattern).find_next_sibling("dd").text.strip()

    return data

  def _scrapCompanies(self):
    for companyName in self.companyNames:
      companyData = self._scrapData(companyName)
      self.data[companyName] = companyData

  def scrap(self):
    self.login()
    self._scrapCompanies()
    self.logout()
    
  def scrapFromLocal(self):
    self._scrapCompanies()

  def to_json(self, filename=None):
    if filename:
      with open(filename, 'w') as f:
        json.dump(self.data, f)
    else:
      return json.dumps(self.data)

  def to_csv(self, filename=None):
    df = pd.DataFrame.from_dict(self.data, orient="index")
    if filename:
      df.to_csv(filename, index_label="Company", encoding='utf-8')
    else:
      return df.to_csv()

  def to_markdown(self, filename=None):
    df = pd.DataFrame.from_dict(self.data, orient="index")
    if filename:
      with open(filename, 'w') as f:
        df.to_markdown(f)
    else:
      return df.to_markdown()


ss = SalesScraper('johandry@yahoo.com', 'NataL1nda', 
                  companyNames=['salesforce', 'vmware'], 
                  fields=['Company size', 'Website', 'Headquarters', 'Industry'])

localSource = True
if localSource:
  ss.savePages(overwrite=False)
  ss.scrapFromLocal()
else:
  ss.scrap()

ss.to_csv('output.csv')
ss.to_markdown('output.md')
print(ss.to_json())


# Notes:
# Download driver from: https://chromedriver.chromium.org/downloads
