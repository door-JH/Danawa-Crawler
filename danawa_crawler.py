# -*- coding: utf-8 -*-

# danawa_cralwer.py
# sammy310


from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from datetime import datetime
from datetime import timedelta
from pytz import timezone
import csv
import os
import os.path
import shutil
import traceback

from multiprocessing import Pool

from github import Github

IS_TEST = False
# IS_TEST = True

PROCESS_COUNT = 2

GITHUB_TOKEN_KEY = 'MY_GITHUB_TOKEN'
GITHUB_REPOSITORY_NAME = 'door-JH/Danawa-Crawler'

CRAWLING_DATA_CSV_FILE = 'CrawlingCategory.csv'
if IS_TEST:
    CRAWLING_DATA_CSV_FILE = 'CrawlingCategory_test.csv'

DATA_PATH = 'crawl_data'
DATA_REFRESH_PATH = f'{DATA_PATH}/Last_Data'

TIMEZONE = 'Asia/Seoul'

CHROMEDRIVER_PATH = 'chromedriver'
if IS_TEST:
    CHROMEDRIVER_PATH = 'chromedriver_112.exe'

DATA_DIVIDER = '---'
DATA_REMARK = '//'
DATA_ROW_DIVIDER = '_'
DATA_PRODUCT_DIVIDER = '|'

STR_NAME = 'name'
STR_URL = 'url'
STR_CRAWLING_PAGE_SIZE = 'crawlingPageSize'


class DanawaCrawler:
    def __init__(self):
        self.errorList = list()
        self.crawlingCategory = list()
        with open(CRAWLING_DATA_CSV_FILE, 'r', newline='') as file:
            for crawlingValues in csv.reader(file, skipinitialspace=True):
                if not crawlingValues[0].startswith(DATA_REMARK):
                    self.crawlingCategory.append({STR_NAME: crawlingValues[0], STR_URL: crawlingValues[1], STR_CRAWLING_PAGE_SIZE: int(crawlingValues[2])})

    def StartCrawling(self):
        self.chrome_option = Options()
        self.chrome_option.add_argument('--headless')
        self.chrome_option.add_argument('--window-size=1920x1080')
        self.chrome_option.add_argument('--start-maximized')
        self.chrome_option.add_argument('--disable-gpu')
        self.chrome_option.add_argument('lang=ko=KR')
        custom_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        self.chrome_option.add_argument(f'user-agent={custom_user_agent}')
        self.chrome_option.add_argument('--no-sandbox')
        self.chrome_option.add_argument('--disable-dev-shm-usage')


        if __name__ == '__main__':
            pool = Pool(processes=PROCESS_COUNT)
            pool.map(self.CrawlingCategory, self.crawlingCategory)
            pool.close()
            pool.join()

            
    
    def CrawlingCategory(self, categoryValue):
        crawlingName = categoryValue[STR_NAME]
        crawlingURL = categoryValue[STR_URL]
        crawlingSize = categoryValue[STR_CRAWLING_PAGE_SIZE]

        print('Crawling Start : ' + crawlingName)

        # data
        crawlingFile = open(f'{crawlingName}.csv', 'w', newline='', encoding='utf8')
        crawlingData_csvWriter = csv.writer(crawlingFile)
        crawlingData_csvWriter.writerow([self.GetCurrentDate().strftime('%Y-%m-%d %H:%M:%S')])
        
        try:
            # browser = webdriver.Chrome(CHROMEDRIVER_PATH, options=self.chrome_option)
            browser = webdriver.Chrome(options=self.chrome_option)
            browser.implicitly_wait(5)
            browser.get(crawlingURL)
            self.CloseOverlayElements(browser)

            browser.execute_script("document.querySelectorAll('modal-widget').forEach(e => e.remove())")
            browser.find_element(By.XPATH, '//option[@value="90"]').click()
        
            wait = WebDriverWait(browser, 10)
            wait.until(EC.invisibility_of_element((By.CLASS_NAME, 'product_list_cover')))
            
            for i in range(-1, crawlingSize):
                self.CloseOverlayElements(browser)
                if i == -1:
                    self.ClickElementSafely(browser, By.XPATH, '//li[@data-sort-method="NEW"]')
                elif i == 0:
                    self.ClickElementSafely(browser, By.XPATH, '//li[@data-sort-method="BEST"]')
                elif i > 0:
                    if i % 10 == 0:
                        self.ClickElementSafely(browser, By.XPATH, '//a[@class="edge_nav nav_next"]')
                    else:
                        self.ClickElementSafely(browser, By.XPATH, '//a[@class="num "][%d]'%(i%10))
                wait.until(EC.invisibility_of_element((By.CLASS_NAME, 'product_list_cover')))
                
                # Get Product List
                productListDiv = browser.find_element(By.XPATH, '//div[@class="main_prodlist main_prodlist_list"]')
                products = productListDiv.find_elements(By.XPATH, '//ul[@class="product_list"]/li')

                for product in products:
                    if not product.get_attribute('id'):
                        continue

                    # ad
                    if 'prod_ad_item' in product.get_attribute('class').split(' '):
                        continue
                    if product.get_attribute('id').strip().startswith('ad'):
                        continue

                    productId = product.get_attribute('id')[11:]
                    productName = self.ExtractProductName(product)
                    productPriceStr = self.ExtractProductPriceStr(product)
                    
                    crawlingData_csvWriter.writerow([productId, productName, productPriceStr])

        except Exception as e:
            print('Error - ' + crawlingName + ' ->')
            print(traceback.format_exc())
            self.errorList.append(crawlingName)

        crawlingFile.close()

        print('Crawling Finish : ' + crawlingName)

    def CloseOverlayElements(self, browser):
        try:
            browser.execute_script("""
                var selectors = [
                    'button[class*="close"]',
                    'button.close',
                    '.button__close',
                    '.btn_close',
                    '.btn_service_close',
                    '.layer__user-recent button',
                    '.layer-prod-pdb1 button',
                    '[role="dialog"] button'
                ];
                selectors.forEach(function(sel){
                    var elems = document.querySelectorAll(sel);
                    for (var i = 0; i < elems.length; i++) {
                        try { elems[i].click(); } catch (e) {}
                    }
                });
            """)
        except Exception:
            pass

    def ClickElementSafely(self, browser, by, value):
        try:
            element = WebDriverWait(browser, 5).until(EC.element_to_be_clickable((by, value)))
            browser.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            element.click()
        except Exception:
            try:
                browser.execute_script("arguments[0].click();", element)
            except Exception:
                pass

    def ExtractProductName(self, product):
        selectors = [
            (By.CSS_SELECTOR, 'a.prod_name'),
            (By.CSS_SELECTOR, 'p.prod_name'),
            (By.CSS_SELECTOR, 'a[href*="info"]'),
            (By.XPATH, './/a[contains(@class, "prod_name")]'),
            (By.XPATH, './/p[contains(@class, "prod_name")]'),
            (By.XPATH, './/a[contains(@href, "info") and not(@class="") ]'),
        ]

        for by, value in selectors:
            try:
                element = product.find_element(by, value)
                text = element.text.strip()
                if text:
                    return text
            except (NoSuchElementException, StaleElementReferenceException):
                continue

        return ''

    def ExtractProductPriceStr(self, product):
        priceCandidates = [
            (By.CSS_SELECTOR, 'div.price_sect a strong'),
            (By.CSS_SELECTOR, 'div.price_sect strong'),
            (By.CSS_SELECTOR, 'div.price_sect em'),
            (By.XPATH, './/div[contains(@class, "price_sect")]//strong'),
            (By.XPATH, './/div[contains(@class, "price_sect")]//em'),
            (By.XPATH, './/div[contains(@class, "price_sect")]//span'),
            (By.XPATH, './/p[contains(@class, "price")]//strong'),
            (By.XPATH, './/a[contains(@class, "price")]//strong'),
        ]

        for by, value in priceCandidates:
            try:
                elements = product.find_elements(by, value)
                if elements:
                    priceTexts = []
                    for element in elements:
                        text = element.text.strip()
                        if text:
                            priceTexts.append(text)
                    if priceTexts:
                        return DATA_PRODUCT_DIVIDER.join(priceTexts)
            except (NoSuchElementException, StaleElementReferenceException):
                continue

        return ''

    def RemoveRankText(self, productText):
        if len(productText) < 2:
            return productText
        
        char1 = productText[0]
        char2 = productText[1]

        if char1.isdigit() and (1 <= int(char1) and int(char1) <= 9):
            if char2 == '위':
                return productText[2:].strip()
        
        return productText

    def DataSort(self):
        print('Data Sort\n')

        for crawlingValue in self.crawlingCategory:
            dataName = crawlingValue[STR_NAME]
            crawlingDataPath = f'{dataName}.csv'

            if not os.path.exists(crawlingDataPath):
                continue

            crawl_dataList = list()
            dataList = list()
            
            with open(crawlingDataPath, 'r', newline='', encoding='utf8') as file:
                csvReader = csv.reader(file)
                for row in csvReader:
                    crawl_dataList.append(row)
            
            if len(crawl_dataList) == 0:
                continue
            
            dataPath = f'{DATA_PATH}/{dataName}.csv'
            if not os.path.exists(dataPath):
                file = open(dataPath, 'w', encoding='utf8')
                file.close()
            with open(dataPath, 'r', newline='', encoding='utf8') as file:
                csvReader = csv.reader(file)
                for row in csvReader:
                    dataList.append(row)
            
            
            if len(dataList) == 0:
                dataList.append(['Id', 'Name'])
                
            dataList[0].append(crawl_dataList[0][0])
            dataSize = len(dataList[0])
            
            for product in crawl_dataList:
                if not str(product[0]).isdigit():
                    continue
                
                isDataExist = False
                for data in dataList:
                    if data[0] == product[0]:
                        if len(data) < dataSize:
                            data.append(product[2])
                        isDataExist = True
                        break
                
                if not isDataExist:
                    newDataList = ([product[0], product[1]])
                    for i in range(2,len(dataList[0])-1):
                        newDataList.append(0)
                    newDataList.append(product[2])
                
                    dataList.append(newDataList)
                
            for data in dataList:
                if len(data) < dataSize:
                    for i in range(len(data),dataSize):
                        data.append(0)
                
            
            productData = dataList.pop(0)
            dataList.sort(key= lambda x: x[1])
            dataList.insert(0, productData)
                
            with open(dataPath, 'w', newline='', encoding='utf8') as file:
                csvWriter = csv.writer(file)
                for data in dataList:
                    csvWriter.writerow(data)
                file.close()
                
            if os.path.isfile(crawlingDataPath):
                os.remove(crawlingDataPath)

    def DataRefresh(self):
        dTime = self.GetCurrentDate()
        if dTime.day == 1:
            print('Data Refresh\n')

            if not os.path.exists(DATA_PATH):
                os.mkdir(DATA_PATH)
            
            dTime -= timedelta(days=1)
            dateStr = dTime.strftime('%Y-%m')

            dataSavePath = f'{DATA_REFRESH_PATH}/{dateStr}'
            if not os.path.exists(dataSavePath):
                os.mkdir(dataSavePath)
            
            for file in os.listdir(DATA_PATH):
                fileName, fileExt = os.path.splitext(file)
                if fileExt == '.csv':
                    filePath = f'{DATA_PATH}/{file}'
                    refreshFilePath = f'{dataSavePath}/{file}'
                    shutil.move(filePath, refreshFilePath)
    
    def GetCurrentDate(self):
        tz = timezone(TIMEZONE)
        return (datetime.now(tz))

    def CreateIssue(self):
        if len(self.errorList) > 0:
            g = Github(os.environ[GITHUB_TOKEN_KEY])
            repo = g.get_repo(GITHUB_REPOSITORY_NAME)
            
            title = f'Crawling Error - ' + self.GetCurrentDate().strftime('%Y-%m-%d')
            body = ''
            for err in self.errorList:
                body += f'- {err}\n'
            labels = [repo.get_label('bug')]
            repo.create_issue(title=title, body=body, labels=labels)
        


if __name__ == '__main__':
    crawler = DanawaCrawler()
    crawler.DataRefresh()
    crawler.StartCrawling()
    crawler.DataSort()
    crawler.CreateIssue()
