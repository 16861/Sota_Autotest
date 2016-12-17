#!/usr/bin/python3

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


from time import sleep, time
from datetime import datetime
import random, sqlite3, re


DBNAME = "sota.sdb"

#sign statuses
DIR = 1
DIR_SIGN = 2
BUH_DIR_SIGN = 3

class DBSota:
    def __init__(self):
        self._dbname = DBNAME


    def _exec(self, script):
        '''
        returns cursor on 
        '''
        ret = None
        with sqlite3.connect(self._dbname) as db:
            ret = db.execute(script)
        return ret

    def _getCurTime(self):
        return datetime.now().strftime("%d-%m-%y_%I:%M:%S")

    def _initScripts(self):
        init = '''
            CREATE TABLE IF NOt EXISTS querycharcodes(
                charcode VARCHAR(12) NOT NULL UNIQUE
            );
        '''


    def initScript(self):
        self._exec('''
        CREATE TABLE IF NOT EXISTS createddocs(
            cardcode VARCHAR(20) NOT NULL UNIQUE,
            charcode VARCHAR(10) NOT NULL,
            sessionid VARCHAR(40) NOT NULL,
            time VARCHAR(20) NOT NULL
        );
        ''')

    @property
    def createddocs(self):
        return [x for x in self._exec('select * from createddocs;')]

    @createddocs.setter
    def createddocs(self, values):
        # 
        # accept a dict as an input argument
        # 
        #add only unique cardcodes
        for ch in self._exec('select cardcode from createddocs;'):
            if ch[0] == values['cardcode']:
                return
        
        self._exec("insert into createddocs values('{0}','{1}','{2}','{3}');".format(values["cardcode"],
        values["charcode"], values["sessionid"], self._getCurTime()))

        self._createddocs = [x for x in self._exec('select * from createddocs;')]

    @createddocs.deleter
    def createddocs(self):
        self._exec("delete from createddocs;")
        del(self._createddocs)

    

    @property
    def querycharcodes(self):
        return [x for x in self._exec('select * from querycharcodes;')]

    @querycharcodes.setter
    def querycharcodes(self, charcode):
        #add only unique charcode
        for ch in self._exec('select * from querycharcodes;'):
            if ch[0] == charcode:
                return

        self._exec("insert into querycharcodes values('" + str(charcode) + "');")
        self._querycharcodes = [x for x in self._exec('select * from querycharcodes;')] 

    @querycharcodes.deleter
    def querycharcodes(self):
        self._exec("delete from querycharcodes;")
        del(self._querycharcodes)
        




class Sota:
    
    class Doc:
        def __init__(self, cardcode = None, charcode = None, owner = None):
            self.cardcode = cardcode
            self.charcode = charcode
            self.owner = owner

        @property
        def cardcode(self):
            return self.cardcode
        
        @cardcode.setter
        def cardcode(self, val):
            self.cardcode = val

        @property
        def charcode(self):
            return self.charcode
        
        @cardcode.setter
        def charcode(self, val):
            self.charcode = val

        @property
        def owner(self):
            return self.owner
        
        @cardcode.setter
        def owner(self, val):
            self.owner = val

        
    class Report(Doc):
        def getDocUrl(self):
            return "http://sota-buh.com.ua/reporting/opendoc?cardCode=" + self.cardcode + "&path=reporting"
        
    
    def __init__(self, page="https://onlinesrv.office.intelserv.com:100/", dev = True):
        self._site = page
        capabilities = DesiredCapabilities.CHROME
        capabilities['loggingPrefs'] = { 'browser':'ALL' }
        self.driver = webdriver.Chrome('/home/espadon/programming/Sota_Autotest/WebDrivers/chromedriver', desired_capabilities=capabilities)
        self.driver.set_page_load_timeout(20)
        self.driver.get(page)
        self._logging("Starting webdriver...")
        
        self._subMenus = {'reporting': 'Звіти - СОТА', 
        'govqry': 'Інформаційна довідка - СОТА', 
        'primarydocs': 'Реєстр первинних документів - СОТА', 
        'persons': 'Співробітники - СОТА',
        'enterprise': 'Підприємство - СОТА' }
        
        if self.driver.title.lower().startswith('ошибка сертификата') and dev:
            self.driver.find_element_by_name('overridelink').send_keys(Keys.RETURN)

        #create log file
        with open('log.lg', 'w') as fd:
            pass

        #name of db
        self._db = DBSota()
        # self._db.initScript()
        self.createdDocs = []

        self._docStatuses = (1, #uncheck
        2, #checked no error
        3, #checked, errors exists
        4, #signed
        )

    
    def _closePopUp(self):
        try:
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'popup-window-head'))
            )
            self.driver.find_element_by_id('popup_ok').click()
            return True
        except:
            return False
    
    def _logging(self, mes):
        #logging steps into a file
        with open('log.lg', 'a') as fd:
            fd.write(datetime.now().strftime("%d-%m-%y_%I:%M:%S") + ' '  + str(mes) + "\n")
            
    def _getAllChcodes(self):
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

    def _getCardcode(self):
        try:
            return re.search('[0-9]+', self.driver.current_url).group(0)
        except:
            return None

    def _fillNN(self):
        self.driver.find_element_by_xpath('//div[@class="fc N2_11"]').click()

    def _sendDoc(self, sign_status):
        def sign():
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//input[@autocomplete=\"off\"]"))
            ).send_keys('123')
            self.driver.find_element_by_class_name("ok-button").click()

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "certList"))
                )
                self.driver.find_element_by_xpath("//table[@id=\"certList\"]/tbody/tr/td[contains(text(), \"Директор\")]").click()
                self.driver.execute_script("document.getElementsByClassName('ok-button')[1].click()")
              
            except:
                self.driver.execute_script("document.getElementsByClassName('ok-button')[1].click()")

        doc_status =  self.driver.find_element_by_xpath("//div[@id=\"docActions\"]/div[@class=\"document-status has-error\"]").get_attribute('innerHTML')
        print("Doc: " + doc_status)

        if "готовий до подачі" in doc_status:
            return

        try:
            self.driver.find_element_by_xpath("//a[@data-docaction=\"check\"]").click()
        except:
            pass

        sleep(1)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//a[@data-docaction=\"forsign\"]"))
            ).click()
        except:
            self.driver.find_element_by_xpath("//a[@data-docaction=\"sign\"]").click()
        
        if sign_status == DIR:
            sign()
        elif sign_status == DIR_SIGN:
            sign()
        else:
            sign()


    def _getCharcodeOfDoc(self):
        try:
            return self.driver.find_element_by_xpath("//div[@class=\"breadcrumbs\"]/ul/li[2]/a").get_attribute('innerHTML')
        except:
            return None

    def _getDocStatus(self):
        doc_status =  self.driver.find_element_by_xpath("//div[@id=\"docActions\"]/div[@class=\"document-status has-error\"]").get_attribute('innerHTML')
        if "Документ готується" in doc_status:
            return 1
        elif "не містить помилок" in doc_status:
            return 2
        elif "Документ містить помилки" in doc_status:
            return 3
        else:
            return 4
    
    def _getFiltersList(self):
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'datatables-filter-row'))
        )

        return self.driver.find_elements_by_xpath('//tr[@class="datatables-filter-row"]/th')

    def _getContentOfTable(self):
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'dataTables_scrollBody'))
        )
        return self.driver.find_elements_by_xpath("//div[@class=\"dataTables_scrollBody\"]/table/tbody/tr")


    def _openReport(self, cardcode):
        self.driver.get(self._site + "/reporting/opendoc?cardCode=" + cardcode)
        
    def getSessionID(self):
        return self.driver.session_id

    def getCurrentOrg(self):
        while True:
            elm = self.driver.find_element_by_xpath("//div[@class=\"list-companies\"]/a[@class=\"user-logined\"]").get_attribute('innerHTML')
            edrpou = re.search("[0-9]+", elm).group(0)

            if edrpou != '3434343434':
                break
            sleep(2)

 

        return edrpou

    def getOrgsdqWithMail(self):
        WebDriverWait(self.driver, 15).until (
            EC.presence_of_element_located((By.CLASS_NAME, "notification"))
        ).click()

        WebDriverWait(self.driver, 15).until (
            EC.presence_of_element_located((By.CLASS_NAME, "notification-table"))
        )

        return_list = []

        for elm in self.driver.find_elements_by_xpath("//td[@class=\"notification-text\"]/p/span"):
            if len(re.search("[0-9]+", elm.get_attribute('innerHTML')).group(0)) in [10, 8]:
                return_list.append(re.search("[0-9]+", elm.get_attribute('innerHTML')).group(0))

        return return_list




    
    def goTo(self, subMenu):
        if subMenu in self._subMenus.keys():
            self.driver.find_element_by_class_name("submenu-icon").click()
            self.driver.find_element_by_xpath("//a[@href=\"/"+subMenu+"\"]").send_keys(Keys.RETURN)
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.title_is(self._subMenus[subMenu])
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

        # with sqlite3.connect(DB_NAME) as con:
        #     cur = con.execute("SELECT sign_status FROM users WHERE phone = '{0}';".format(phone))
        #     if cur.rowcount == -1:
        #         con.execute("insert into users(phone, password) values('{0}', '{1}');".format(phone, pass_))
                
        # self._user_name = phone
        
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


        #self.recieveMsg()

    def recieveMsg(self, edrpou = None):
        if not edrpou:
            edrpou = self.getCurrentOrg()

        if edrpou in self.getOrgsWithMail():
            self.driver.find_element_by_xpath("//td[@class=\"notification-text\"]/p/span[contains(text(), \"" + edrpou + "\")]").click()
            if self._closePopUp():
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, 'CryptoNotFounddWindow'))
                )
                
                # self.driver.find_element_by_xpath("//div[@class=\"popup-window-head\"]/span[@class=\"popup-icon-close\"]").click()
                
        else:
            print(False)


    def createReport(self, charcode = 'J0200118'):
        if not self.driver.title.lower().startswith("звіти"):
            self.goTo('reporting')
        self.driver.find_element_by_class_name('add-icon').click() 
        self.driver.find_element_by_xpath("//tr[@class=\"datatables-filter-row\"]/th/div/label/input[@type=\"text\"]").send_keys(charcode[:4])
        list_filtered_reports = self.driver.find_elements_by_xpath("//table[@id=\"selTmplGrid\"]/tbody/tr/td[@class=\"sorting_1\"]") # getting all available charcodes
        
        for el in list_filtered_reports:
            if charcode in str(el.get_attribute('innerHTML')):
                el.click()
                break

        newDoc.append(Report(self._getCardcode(), charcode))
        self._logging("Created report: charcode " + charcode + ", cardcode " + self._getCardcode())

                
    def createQuery(self, charcode='All'):
        
        if not self.driver.title.lower().startswith("вибір документа"):
            if not self.driver.title.lower().startswith("інформаційна довідка"):
                self.goTo('govqry')
              
        self.driver.find_element_by_class_name('add-icon').click()

        
        
        if charcode == "All":
            list_of_chcodes = self._getAllChcodes()
            print(list_of_chcodes)
        else:
            list_of_chcodes = [charcode]
        
        for code in list_of_chcodes:
            for el in self.driver.find_elements_by_xpath("//table[@id=\"selTmplGrid\"]/tbody/tr/td[@class=\"sorting_1\"]"):
                if code in str(el.get_attribute('innerHTML')):
                    self._logging("creating document with charocode: " + str(el.get_attribute('innerHTML')))
                    el.click()
                    break

            sleep(2)
            self._db.createddocs = {'cardcode': self._getCardcode(), 'charcode': self._getCharcodeOfDoc(), 'sessionid': self.getSessionID() }
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID,'newReport'))
            ).click()
        
        self.goTo('govqry')

    def copyCrtQuery(self):
        for cardcode in self.createdDocs:
            self._openReport(cardcode)
            sleep(2)
            self.driver.find_element_by_class_name("copy-icon").click()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'periodSelectWindow'))
            )
            sleep(2)

    def printCrtQuery(self):
        for cardcode in self.createdDocs:
            self._openReport(cardcode)
            sleep(2)
            self.driver.execute_script("document.getElementsByClassName('print-icon')[0].click()")
            sleep(3)
           

    def fillSendQuery(self, cardcode = None, sign_status = DIR):
        if not cardcode:
            return 

        self.driver.get("https://sota-buh.com.ua/reporting/opendoc?cardCode=" + cardcode + "&path=govqry")

        
        charcode = self._getCharcodeOfDoc()
        if charcode == 'J1300104':
            try:

                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[@p=\"N5\"]"))
                ).click()
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[@class=\"editor date-editor\"]/input[@type=\"text\"]"))
                ).send_keys("09.12.2016")
                               
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[@p=\"N7\"]"))
                ).click()
            
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "cc"))
                ).click()

                self.driver.find_element_by_xpath("//div[@p=\"N8\"]").click()
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "cc"))
                ).click()

            except TimeoutException:
                pass
        elif charcode == '':
            pass
        

        self._sendDoc(sign_status)


    def createNN(self):
        if not self.driver.title.startswith(self._subMenus['primarydocs']):
            self.goTo('primarydocs')
        
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'add-icon'))
        ).click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'taxBill'))
        ).click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[@class="doc-button check-icon"]'))
        )

        
        self._fillNN()


    def createRK(self, negative=True):
        pass

    def createSourceDoc(self, charcode=None):
        pass

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
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class=\"list-companies\"]"))
        ).click()
        self.driver.find_element_by_xpath("//a[@data-edrpou=\""+ edrpou +"\"]").click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[@class=\"user-logined\" and @data-edrpou=\"' + edrpou + '\"]'))
        )  

    def closeDriver(self):
        self.driver.close()
        exit(0)

    def deleteAllUnsignedReports(self, charcode):
        if not self.driver.title.lower().startswith(self._subMenus['reporting']):
            self.goTo('reporting')
        
        #mark all delted reports
        reports = self.driver.find_elements_by_css_selector(".child-rows-control.has-child-rows")
        print(reports)
        # reports[0].click()

        checkboxes = self.driver.find_elements_by_class_name(" select-checkbox")
        print("Len: ", len(checkboxes))
        for ch in  checkboxes:
            try:
                print("Loc of el: " + str(ch.location['y'] + ch.size['height']))
                print(str(ch.location['y']) + " " + str(ch.size['height']))
                webdriver.ActionChains(self.driver).move_to_element(ch).click(ch).perform()
                # self.driver.execute_script("window.scrollTo({0},{1});".format(ch.location['x'], ch.size['height']+50))
                # ch.click()
            except:
                print("Loc of el: " + str(ch.location['x'] + ch.size['height']+50))
                print(str(ch.location['y'] + ch.size['height']))
                self.driver.execute_script("window.scrollTo(0,{0});".format(ch.location['y']+50))
                sleep(1)
                ch.click()

    def processReports(self):
        if not self.driver.title.lower().startswith(self._subMenus['reporting']):
            self.goTo('reporting')

        list = self.driver.find_elements_by_xpath("//table[@id=\"reportsTable\"]/tbody/tr")
        print(len(list))

        for el in list:
            attr = el.get_attribute('class')
            if  attr == 'odd' or attr == "even" or attr == "odd gree" or attr == "even green":
                print("Single report or report spoiled report ")
                print("name", re.search("class=\" hover-underline\">(.+?)<", el.get_attribute("innerHTML")).group(1), True)
                try:
                    print("charcode " + re.search("class=\"child-rows-control has-child-rows\"><span></span>(.+?)<", el.get_attribute("innerHTML")).group(1))
                except:
                    print("charcode " + re.search("class=\"  child-rows-control\">(.+?)<", el.get_attribute("innerHTML")).group(1))
                print("status" + re.search(">(Новий|Неприйнятий)<", el.get_attribute("innerHTML")).group(1))
                print("date of modification" + re.search("class=\"dt-body-right sorting_1\">(.+?)<", el.get_attribute("innerHTML")).group(1))

            elif attr == "odd parent" or attr == "even parent":
                print("Open parent report")
                # print(el.find_element_by_xpath(".//td[@class=\"hover-underline.sorting_1\"]").get_attribute("innerHTML"))
            elif attr == "child child-row":
                print("Child rows")
            # print("HTML: " + el.get_attribute('innerHTML'))
            # el.find_element_by_css_selector('')

    def executeCommand(self, command):
        print(self.driver.execute_script(command))

        for entry in self.driver.get_log('browser'):
           print(re.search('[0-9]+:[0-9]+ (.+)', entry['message']).group(1))


class Enterprise:
    def __init__(self, welement = None, name = None, edrpou = None, license = None, status = None):
        self._elem = welement
        self._name = name
        self._edrpou = edrpou
        self._license = license
        self._status = status

    @property
    def elem(self):
        return self._elem

    @elem.setter
    def elem(self, val):
        self._elem = val

    @elem.deleter
    def elem(self):
        del self._elem        
    
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = val

    @name.deleter
    def name(self):
        del self._name

    @property
    def edrpou(self):
        return self._edrpou

    @edrpou.setter
    def edrpou(self, val):
        self._sedrpou = val

    @edrpou.deleter
    def edrpou(self):
        del self._edrpou

    @property
    def license(self):
        return self._license

    @license.setter
    def license(self, val):
        self._license = val

    @license.deleter
    def license(self):
        del self._license

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, val):
        self._status = val

    @status.deleter
    def status(self):
        del self._status

    def __str__(self):
        return "Edrpou: {0}\nName: {1} \nLicense: {2} \nStatus: {3} \n".format(self._edrpou, self._name, self._license, self._status)

class Enterprises(Sota):

    def getListOfEnterprises(self):
        if not self.driver.title.lower().startswith(self._subMenus['enterprise']):
            self.goTo('enterprise')

        self.cur_enterprises = []

        for el in self.driver.find_elements_by_xpath('//table[@id=\"orgs\"]/tbody/tr'):
            html = el.get_attribute('innerHTML')
            attr = [y.replace('<td class="sorting_1">', '')  for y in re.findall('td>(.+?)</td', html)]
            self.cur_enterprises.append(Enterprise(el, attr[1], attr[0], attr[2], attr[3]))

        # [print(e) for e in self.cur_enterprises]

        return self.cur_enterprises

    def goToEnterprise(self, edrpou):
        if not self.driver.title.lower().startswith(self._subMenus['enterprise']):
            self.goTo('enterprise')

        list = self.getListOfEnterprises()
        for ent in list:
            if ent.edrpou == edrpou:
                ent.elem.find_element_by_class_name('sorting_1').click()
                WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[@class=\"breadcrumbs\"]/ul/li/a[contains(text(), \"" + edrpou +  "\")]"))
                )
                break

    def testDicts(self):
        # open dicts in modal window

        start_time = time()
        
        for dict_el in self.driver.find_elements_by_xpath("//span[@class=\"dictionary-field-icons\"]"):
            dict_el.find_element_by_xpath(".//img[@alt=\"select\"]").click()

            #select various item count
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'dataTables_length'))
            )
            show_records = self.driver.find_elements_by_xpath("//div[@class=\"dataTables_length\"]/label/select/option")

            for el in show_records[1:]:
                el.click()
                sleep(3) #check result
            show_records[0].click()
            sleep(2) #waiting while page is reloading


            filter_list = self._getFiltersList()
            list_of_content = []
            for el in self._getContentOfTable():
                list_of_content.append(re.findall('>([^<>].+?)<', el.get_attribute('innerHTML')))

            n = 0
            for filter in filter_list:
                try:
                    filter.find_element_by_xpath('.//input[@type="text"]').send_keys(list_of_content[1][n])
                    n = n+1
                    sleep(2)
                    filter.find_element_by_xpath('.//input[@type="text"]').clear()
                except:
                    continue
            sleep(2)
            self.driver.execute_script("document.getElementsByClassName('ok-button')[0].click()")

            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//span[@class=\"dictionary-field-icons\"]"))
            )
            input_field = dict_el.find_element_by_xpath(".//input[@autocomplete=\"off\"]")
            input_field.send_keys(list_of_content[1][1][:4])
            sleep(2)
            input_field.send_keys(Keys.DOWN)
            input_field.send_keys(Keys.UP)
            sleep(2)
            input_field.send_keys(Keys.RETURN)

        # self.driver.find_element_by_class_name('save-icon').click()

        print("Time of execution: ", time() - start_time)
            
            
     
            


new_test = Enterprises(page="https://sota-buh.com.ua")
new_test.login()
# new_test.getListOfEnterprises()
new_test.goToEnterprise('36936969')
new_test.testDicts()
sleep(2)
new_test.closeDriver()
# sota = Sota(page="https://sota-buh.com.ua")
# sota.login()
# sota.goTo('enterprise')
# sota.processReports()
# sota.goTo('reporting')
# sota.executeCommand('''x = document.getElementsByClassName('select-checkbox'); for (var i = 0; i < x.length; i++) {
#    x[i].click(); //second console output
# }''')
# sota.executeCommand("document.getElementsByClassName('select-checkbox')")
# sota.executeCommand("console.log(21321312)")
# sota.executeCommand("console.log('Messsage')")

# sleep(3)
# sota.closeDriver()


# sota.copyCrtQuery()
# sota.printCrtQuery()
# sota.recieveMsg()

# sota.changeOrg('38267550')
# sota.fillSendQuery("17168120")
# sota.changeOrg('34554355')