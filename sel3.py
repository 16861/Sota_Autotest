#!/usr/bin/python3

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC


from time import sleep
from datetime import datetime
import sys, codecs, random, sqlite3


class Sota:
    """

    """
    def __init__(self, page="https://onlinesrv.office.intelserv.com:100/", dev = True):
        self.driver = webdriver.Chrome('/home/espadon/programming/Sota_Autotest/WebDrivers/geckodriver')
        self.driver.set_page_load_timeout(20)
        self.driver.get(page)
        self._logging("Starting webdriver...")
        
        self._subMenus = ['reporting', 'govqry', 'persons']
        
        if self.driver.title.lower().startswith('ошибка сертификата') and dev:
            self.driver.find_element_by_name('overridelink').send_keys(Keys.RETURN)

        #create log file
        with open('log.lg', 'w') as fd:
            pass
    
    def _closePopUp(self):
        try:
            self.driver.find_element_by_class('popup-window-head');
            self.driver.find_element_by_class('popup-icon-close').click();
        except:
            pass
    
    def _logging(self, mes):
        #logging steps into a file
        with open('log.lg', 'a') as fd:
            fd.write(datetime.now().strftime("%d-%m-%y_%I:%M:%S") + ' '  + str(mes) + "\n")
            
    def _get_all_chcode(self):
        ret = []
        # sleep(3)
        for el in self.driver.find_elements_by_xpath("//table[@id=\"selTmplGrid\"]/tbody/tr/td[@class=\"sorting_1\"]"):
            ret.append(el.get_attribute('innerHTML'))
        
        return ret
        
    def _getRandomDate(self):
        def twoDigit(x):
            if len(x) == 1:
                return '0' + x
            return x
    
        day = twoDigit(str(random.randint(1, 31)))
        mon = twoDigit(str(random.randint(1, 12)))
        # year = '2015'
        
        return day + mon + '2015'
    
    def goTo(self, subMenu):
        if subMenu in self._subMenus:
            self.driver.find_element_by_class_name("submenu-icon").click()
            self.driver.find_element_by_xpath("//a[@href=\"/"+subMenu+"\"]").send_keys(Keys.RETURN)
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.title_is('Співробітники - СОТА')
                )
            except:
                print("Can't load page! Trying to go to " + subMenu)
                self._logging("Can't load page! Trying to go to " + subMenu)
                self.driver.quit()
                exit(1)
            self._logging("In " + subMenu + " now")
        else:
            self._logging("Wrong submenu or it is not operational now: " + subMenu)
        
    def login(self, name='997174743', userPass='111222'):
        self.driver.find_element_by_xpath("//a[@href=\"/account/login\"]").send_keys(Keys.RETURN)

        phone = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'Phone'))
        )
        pass_ = self.driver.find_element_by_name('Password')
        phone.send_keys(name)
        pass_.clear()
        pass_.send_keys(userPass)
        
        pass_.send_keys(Keys.RETURN)
        
        try:
            WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class=\"enter-top\"]/a[@class=\"user-logined\"]'))
            )
            self._logging("Successfull login into account")
        except:
            self._logging("Can't login!")
            self.driver.quit()
            exit(1)


    def createReport(self, charcode = 'J0200118'):
        if not self.driver.title.lower().startswith("вибір звіту"):
            if not self.driver.title.lower().startswith("звіти"):
                self.goTo('reporting')
            self.driver.find_element_by_class_name('add-icon').click() 
        self.driver.find_element_by_xpath("//tr[@class=\"datatables-filter-row\"]/th/div/label/input[@type=\"text\"]").send_keys(charcode[:4])
        list_filtered_reports = self.driver.find_elements_by_xpath("//table[@id=\"selTmplGrid\"]/tbody/tr/td[@class=\"sorting_1\"]") # getting all available charcodes
        
        for el in list_filtered_reports:
            if charcode in str(el.get_attribute('innerHTML')):
                el.click()
                break
                

                
    def createQuery(self, charcode='All'):
        
        if not self.driver.title.lower().startswith("вибір документа"):
            if not self.driver.title.lower().startswith("інформаційна довідка"):
                self.goTo('govqry')
              
        self.driver.find_element_by_class_name('add-icon').click()

        
        
        if charcode == "All":
            list_of_chcodes = self._get_all_chcode()
        else:
            list_of_chcodes = [charcode]
        
        for code in list_of_chcodes:
            for el in self.driver.find_elements_by_xpath("//table[@id=\"selTmplGrid\"]/tbody/tr/td[@class=\"sorting_1\"]"):
                if code in str(el.get_attribute('innerHTML')):
                    self._logging("creating document with charocode: " + str(el.get_attribute('innerHTML')))
                    el.click()
                    break
            # sleep(5)
            self.driver.find_element_by_class_name('add-icon').click()
        
        self.goTo('govqry')

    def createPerson(self):
        if not self.driver.title.lower().startswith("співробітники"):
            self.goTo('persons')
              
        self.driver.find_element_by_class_name('add-icon').click()
        
        #filling mandatory fields
        WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.ID, "LastName"))
                ).send_keys('Asimov')
        self.driver.find_element_by_id('FirstName').send_keys('Isaac')
        self.driver.find_element_by_id('Num').send_keys(str(random.sample(range(1,11), 10)).replace('[', '').replace(', ', '').replace(']', ''))


        
        while True:
            self.driver.find_element_by_id("BirthDate").send_keys(self._getRandomDate())
            self.driver.find_element_by_class_name('save-icon').click()
        
            try:
                self.driver.find_element_by_xpath("//dev[@data-valmsg-summary=\"true\"]")
                self.driver.find_element_by_id("BirthDate").clear()
            except:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//ul[@id=\"PersonsMenu\"]/li[@class=\" \"]/a[contains(text(), \"Додатково\")]"))
                )            
                break
        
        self.driver.find_element_by_xpath("//ul[@id=\"PersonsMenu\"]/li/a[contains(text(), \"Додатково\")]").click()

        WebDriverWait(self.driver,15).until(
                    EC.presence_of_element_located((By.ID, "DateAdd"))
                )

        while True:
            self.driver.find_element_by_id("DateAdd").send_keys(self._getRandomDate())
            self.driver.find_element_by_id("DateEnd").send_keys(self._getRandomDate())
            
            self.driver.find_element_by_class_name('save-icon').click()
            
            try:
                self.driver.find_element_by_xpath("//dev[@class=\"validation-summary-errors\"]/ul/li")
                self.driver.find_element_by_id("BirthDate").clear()
            except:
                # WebDriverWait(self.driver, 20).until(
                    # EC.presence_of_element_located((By.CLASS_NAME, "submenu-icon"))
                # )            
                break
                
        sleep(2)
        self.goTo('persons')
            
        
    def changePeriod(self, month, year):
        self.driver.find_element_by_xpath("//select[@id=\"period\"]/option[@value=\""+  str(month) +"\"]").click()
        self.driver.find_element_by_xpath("//select[@id=\"year\"]/option[@value=\""+  str(year) +"\"]").click()
        
    def changeOrg(self, edrpou):
        # sleep(4)
        self.driver.find_element_by_xpath("//div[@class=\"list-companies\"]").click()
        self.driver.find_element_by_xpath("//a[@data-edrpou=\""+ edrpou +"\"]").click()
        WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//a[@class=\"user-logined\" and @data-edrpou=\"' + edrpou + '\"]'))
            )
        


sota = Sota(page="https://sota-buh.com.ua")
sota.login()
sota.changeOrg('38267550')

sota.goTo('persons')
for _ in range(3):
    sota.createPerson()


# sota.changeOrg('3693693691')
# sota.goTo('govqry')
# sota.createQuery()


# sota.changeOrg('36936969')
# sota.goTo('govqry')
# sota.createQuery()