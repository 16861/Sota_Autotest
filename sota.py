from main import AutotestMain

from time import sleep
from datetime import datetime
import random, re, traceback


DEV = 1
TEST = 2
REAL = 3

class Sota(AutotestMain):
    def __init__(self, page=None, browser = 'chrome', dev = True):
        super().__init__(page, browser, dev)
        
        self._docStatuses = (1, #uncheck
        2, #checked no error
        3, #checked, errors exists
        4, #signed
        )

        if page == DEV:
            self.driver.get('https://onlinesrv.office.intelserv.com:100/')
        elif page == TEST:
            self.driver.get('https://sota-buh.com.ua:8080/')
        elif page == REAL:
            self.driver.get('https://sota-buh.com.ua/')

        self.READY = 4
        self.HAS_ERRORS = 5
        self.HAS_NO_ERRORS = 6
        self.SIGNED = 7

        self.ACTION_DELETE_REP = 10
        self.ACTION_COPY_REP = 20
        self.ACTION_SEND_REP = 30
        self.ACTION_PRINT_REP = 40
        self.ACTION_EXPORT_REP = 50

        self.DEFAULT_SIGN = 0
        self.DIR = 1
        self.BUH = 2

        self._subMenus = { 'primarydocs': 'Реєстр первинних документів - СОТА', 'govqry':'Інформаційна довідка', 'reporting': 'Звіти' }

        #set of signers
        self._saved_signers = set()
        self._signers_dict = ["Директор", "Печатка установи", "Бухгалтер", "Відповідальна особа"]
        self._FOR_DIR = "Директор"
        self._FOR_FIRM_SIGN = "Печатка установи"
        self._FOR_BUH = "Бухгалтер"
        self._FOR_WORKER = "Відповідальна особа"

    def _getAllChcodes(self):
        ret = []
        # sleep(3)
        for el in self.driver.find_elements_by_xpath("//table[@id=\"selTmplGrid\"]/tbody/tr/td[@class=\"sorting_1\"]"):
            ret.append(el.get_attribute('innerHTML'))
        
        return ret
        
    def _getCardcode(self):
        try:
            return re.findall('cardCode=([0-9]+)', self.driver.current_url)[0]
        except:
            return None


    def _sendDoc(self, cardcode=None, path='partner'):
        if cardcode:
            self._openDoc(cardcode)
        
        if path == 'partner':
            err, elem = self._waitFor(self.VISIBILITY, (self.BY_XPATH, ("//a[@data-docaction='sendtopartner']")))
        elif path == 'dfs':
            return False
        else:
            return False
        
        err, elem_ = self._waitFor(self.VISIBILITY, (self.BY_ID, "keyPasswordWindow"))
        if err:
            self._logging("Can't find window keyPass, traceback: {0}".format(err))
            return False
        self.driver.find_element_by_xpath("//input[@autocomplete='off']").send_keys('123')
        self.driver.find_element_by_xpath("//button[@data-action=\"default\"]").click()

        self._waitFor(self.VISIBILITY, (self.BY_ID, 'certListWindow'))
        self.driver.execute_script("document.getElementsByClassName('ok-button')[1].click()")

    def _sendSignDoc(self):
        self._waitFor(self.VISIBILITY, (self.BY_ID, "keyPasswordWindow"))
        self.driver.find_element_by_xpath("//input[@autocomplete='off']").send_keys('123')
        self.driver.find_element_by_xpath("//button[@data-action=\"default\"]").click()

        self._waitFor(self.VISIBILITY, (self.BY_ID, 'certListWindow'))
        self.driver.execute_script("document.getElementsByClassName('ok-button')[1].click()")


        self._signDoc(None)

        
        self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//table[@id=\"addressList\"]/tbody/tr/td[contains(text(), \"gnau_rep2@intelserv.com\")]")).click()
        self.driver.execute_script("document.getElementsByClassName('ok-button')[2].click()")

    def _getCharcodeOfDoc(self):
        bc = self._getBreadcrumbs()
        return bc.find_element_by_xpath("//a[@href='/reporting/opendoc']").get_attribute('innerHTML')
    def _getDocStatus(self):
        err, elem =  self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//div[@id=\"docActions\"]/div[@class=\"document-status\"]"))
        if err:
            err_s, elem = self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//div[@id=\"docActions\"]/div[@class=\"document-status has-error\"]"))
            if err_s:
                self._logging("Can't get doc status!")
                return None
        doc_status = elem.get_attribute('innerHTML')
        if "Документ готується" in doc_status:
            return self.READY
        elif "не містить помилок" in doc_status:
            return self.HAS_NO_ERRORS
        elif "Документ містить помилки" in doc_status:
            return self.HAS_ERRORS
        elif "готовий до подачі" in doc_status or "потрібно підписати" in doc_status or "готовий до відправки" in doc_status :
            return self.SIGNED
        else:
            self._logging("Can't find no item, {0}".format(doc_status))
            return None

    def _getBreadcrumbs(self):
        err, ret = self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//div[@class=\"breadcrumbs\"]/ul/li"))
        if not err:
            return ret
        else:
            self._logging("Can't get breadcrumbs")
    def _openDoc(self, cardcode, charcode = None, submenu = None):
        if not submenu or submenu == 'primarydocs':
            self.driver.get(self._site + "/primarydocs/opendoc?cardCode=" + cardcode)
        elif submenu == 'reporting' or submenu == 'govqry':
            self.driver.get(self._site + "/reporting/opendoc?cardCode=" + cardcode + "&path={0}".format(submenu))

        if charcode:
            err, _ = self._waitFor(self.TITLE_CONTAIN, (charcode))
            if err:
                self._logging("Can't open document with cardcode: {0}, and charcode: {1}".format(cardcode, charcode))
                return False
        self._logging("Successfully open document with cardcode {0}, in primarydoc or default".format(cardcode))
        self._logging("Site: " + self._site + "/reporting/opendoc?cardCode=" + cardcode)
        return True
    def _waitToRcvMsg(self):
        self._waitFor(self.VISIBILITY, (self.BY_ID, "keyPasswordWindow"))
        self.driver.find_element_by_xpath("//input[@autocomplete=\"off\"]").send_keys("123")
        self.driver.find_element_by_xpath("//button[@data-action=\"default\"]").click()
    def _signDoc(self, cardcode=None, saveSigns=False):
        def _setSign():
            def processSigning(person):
                self._logging("Signing for {0}".format(person))

                self.driver.find_element_by_xpath("//input[@autocomplete=\"off\"]").send_keys("123")
                self.driver.find_element_by_xpath("//button[@data-action=\"default\"]").click()
                err, _ = self._waitFor(self.VISIBILITY, (self.BY_ID, 'certListWindow'))
                if not err:
                    self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//table[@id='certList']/tbody/tr/td[contains(text(), \"{0}\")]".format(person)))[1].click()
                else:
                    err, _ = self._waitFor(self.VISIBILITY, (self.BY_ID, 'certInfoWindow'))
                    if err:
                        self._logging("Something went wrong. There are no windows for confirm sign.")
                        return False

                self.driver.execute_script("document.getElementsByClassName('ok-button')[1].click()")
                return True

            err, _ = self._waitFor(self.VISIBILITY, (self.BY_ID, "keyPasswordWindow"))
            if err:
                #
                err, elem_window = self._waitFor(self.VISIBILITY, (self.BY_ID, 'certInfoWindow'))
                if err:
                    self._logging("Signing doc is done")
                    return False  
                person = elem_window.find_element_by_class_name("popup-window-head-title").get_attribute('innerHTML')
                self._logging("Sign for {0} is saved.".format(person))
                self._waitFor(self.VISIBILITY, (self.BY_CLASS_NAME, 'ok-button'))[1].click()
                return True
            else:
                err, elem = self._waitFor(self.VISIBILITY, (self.BY_ID, 'keyCertName'))
                person = elem.get_attribute('innerHTML').strip('"')
            if person in self._signers_dict:
                self._logging("Success!!!!")
                result = processSigning(person)
                if not result:
                    self._logging("Sign is not set!")
                    return False
            else:
                self._logging("Somethin went wrong, again(( Signing for unknown person: {0}, {1}".format(person, self._signers_dict))
                # self._logging("{0}, {1}, {2}".format(person in self._signers_dict, type(person), type(self._signers_dict[2])))
                return False
            
            self._logging('Sign is set')
            return True

        if cardcode:
            self._openDoc(cardcode)
        status = self._getDocStatus()
        # if status != self.SIGNED:
        #     self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//a[@data-docaction='edit']"))[1].click()
        #     self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//a[@data-docaction='check']"))[1].click()

        
        err, elem = self._waitFor(self.VISIBILITY, (self.BY_XPATH, ("//a[@data-docaction='forsign']")))
        if err:
            self._logging("forsign:" + err)
            err_s, elem_s = self._waitFor(self.VISIBILITY, (self.BY_XPATH, ("//a[@data-docaction='sign']")))
            if err_s:
                self._logging("forsign:" + err_s)
                self._logging("Can't click on forsign button, traceback: " + err)
                return False
            elem_s.click()
        else:
            elem.click()

        err, popup = self._waitFor(self.VISIBILITY, (self.BY_ID, 'popup_container'))
        if not err:
            popup.find_element_by_id('popup_ok').click()

        while _setSign():
            pass
        return True
    def getCurrentOrg(self):
        while True:
            elm = self.driver.find_element_by_xpath("//div[@class=\"list-companies\"]/a[@class=\"user-logined\"]").get_attribute('innerHTML')
            edrpou = re.search("[0-9]+", elm).group(0)

            if edrpou != '3434343434':
                break
            sleep(2)

 

        return edrpou

    def getOrgsWithMail(self):
        err, elm = self._waitFor(self.VISIBILITY, (self.BY_CLASS_NAME, "notification"))
        if err:
            self._logging("Can't click on notification button!")
            return None


        self._waitFor(self.VISIBILITY, (self.BY_CLASS_NAME, "notification-table"))

        return_list = []

        for elm in self.driver.find_elements_by_xpath("//td[@class=\"notification-text\"]/p/span"):
            if len(re.search("[0-9]+", elm.get_attribute('innerHTML')).group(0)) in [10, 8]:
                self._logging("find org with mail: " + re.search("[0-9]+", elm.get_attribute('innerHTML')).group(0) )
                return_list.append(re.search("[0-9]+", elm.get_attribute('innerHTML')).group(0))

        return return_list

    
    def goTo(self, subMenu):
        if subMenu in self._subMenus.keys():
            err, element  = self._waitFor(self.VISIBILITY, (self.BY_CLASS_NAME, "submenu-icon"))
            if err:
                self._logging("Can't click on main menu, traceback: \n" + err)
            element.click()

            err, element = self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//a[@href=\"/"+subMenu+"\"]"))
            if err:
                self._logging("Can't click on main menu, traceback: \n" + err)
            element.click()
            err, _ = self._waitFor(self.TITLE_CONTAIN, (self._subMenus[subMenu]))
            if not err:
                self._logging("In " + subMenu + " now")
                return True
            else:
                self._logging("Something went wrong here is your traceback: " + err)
                return None
        else:
            self._logging("Wrong submenu or it is not operational now: " + subMenu)
            return None
        
    def login(self, name='997174743', userPass='111222'):
        err, elem = self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//a[@href=\"/account/login\"]"))
        if err:
            err, _ = self._waitFor(self.VISIBILITY, (self.BY_CLASS_NAME, "user-logined"))
            if not err:
                self._logging("Already loggined in account!")
                return True
            self._logging("Error occured while login into account: " + err)
            return None
        elem.send_keys(self.KEY_RETURN)

        err, phone = self._waitFor(self.VISIBILITY, (self.BY_ID, "Phone"))
        pass_ = self.driver.find_element_by_name('Password')
        phone.send_keys(name)
        pass_.clear()
        pass_.send_keys(userPass)
        
        pass_.send_keys(self.KEY_RETURN)
        

        err, element = self._waitFor(self.VISIBILITY, (self.BY_XPATH, '//div[@class=\"enter-top\"]/a[@class=\"user-logined\"]'))
        if not err:
            self._logging("Successfull login into account")
        else:
            self._logging("Not loggined! Into account: " + name)

        #self.recieveMsg()
    def logout(self):
        self._waitFor(self.VISIBILITY, (self.BY_CLASS_NAME, 'enter-top')).click()
        self._waitFor(self.VISIBILITY, (self.BY_XPATH, '//a[contains(text(), "Вийти")]'), 3).click()

    def recieveMsg(self, edrpou = None, action=None):
        if not edrpou:
            edrpou = self.getCurrentOrg()

        self._logging("Recieving mail for " + edrpou)
        if edrpou in self.getOrgsWithMail():
            
            # if self._closePopUp():
            #     self._waitFor(self.VISIBILITY, (self.BY_ID, 'CryptoNotFounddWindow'))
            state = self.driver.execute_script('return mailer.state.edrpou')
            # self._logging("State: ", state)
            if not state:
                self.driver.find_element_by_xpath("//td[@class=\"notification-text\"]/p/span[contains(text(), \"" + edrpou + "\")]").click()
            err, _ = self._waitFor(self.VISIBILITY, (self.BY_ID, 'keyPasswordWindow'))
            
            if err:
                print("An error ocured while waiting of window to appear: ")
                print(err)
                exit(0)
            if not action:
                self._logging('Not action')
                self.driver.execute_script("for(x = 0; x < document.getElementsByClassName('popup-icon-close').length; x++) document.getElementsByClassName('popup-icon-close')[x].click()")
                self._slp(1)
                err, _ = self._waitFor(self.VISIBILITY, (self.BY_ID, 'keyPasswordWindow'))
                if err:
                    self._logging('Test is done. Password window is closed')
                else:
                    self._logging('Test is failed! Password window is still visible!')


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
        self.driver.find_element_by_id("Ukr_Gromad").click()
        
        
        while True:
            self.driver.find_element_by_id("BirthDate").send_keys(self._getRandomDate())
            self.driver.find_element_by_class_name('save-icon').click()
            if self._browser == 'firefox':
                sleep(1)
        
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[@data-valmsg-summary=\"true\"]"))
                )
                self.driver.find_element_by_id("BirthDate").clear()
                sleep(1)
            except:
                traceback.print_exc()
                WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, "//ul[@id=\"PersonsMenu\"]/li[@class=\" \"]/a[contains(text(), \"Додатково\")]"))
                )            
                break
        
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//ul[@id=\"PersonsMenu\"]/li/a[contains(text(), \"Додатково\")]"))
        ).click()

        

        while True:
            WebDriverWait(self.driver,8).until(
                    EC.presence_of_element_located((By.ID, "DateAdd"))
            ).send_keys(self._getRandomDate())
            self.driver.find_element_by_id("DateEnd").send_keys(self._getRandomDate())
            self.driver.find_element_by_id("WorkBook").click()
            self.driver.find_element_by_id("Spd").click()
            self.driver.find_element_by_id("NotUsed").click()
            self.driver.find_element_by_class_name('save-icon').click()
            
            try:
                WebDriverWait(self.driver, 4).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[@data-valmsg-summary=\"true\"]"))
                )
                self.driver.find_element_by_id("BirthDate").clear()
                sleep(1)
            except:           
                break

        sleep(2)
        self.goTo('persons')
            
        
    def changePeriod(self, month, year):
        err, mon = self._waitFor(self.VISIBILITY, (By.XPATH, "//select[@id=\"period\"]/option[contains(text(), \""+  str(month) +"\")]"))
        if err:
            self._

        self.driver.execute_script('document.getElementsByClassName(\''+ mon.get_attribute('class')  + '\')[0].setAttribute("selected", "selected")')
        if self._browser == 'firefox':
            sleep(0.5)
        self.driver.execute_script("for(i = 21; i <= 23; i++) { document.getElementsByTagName('option')[i].removeAttribute('selected') }")
        self.driver.execute_script("document.getElementsByTagName('option')[{0}].setAttribute('selected', 'selected')".format(int(year)-1994))
        self.driver.execute_script("$('#year').trigger('change')")

        sleep(1)
                
        
    def changeOrg(self, edrpou):
        if self.getCurrentOrg() == edrpou:
            return

        self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//div[@class=\"list-companies\"]"))[1].click()
        self._waitFor(self.VISIBILITY, (self.BY_XPATH, "//a[@data-edrpou=\""+ edrpou +"\"]"))[1].click()
        self._waitFor(self.VISIBILITY, (self.BY_XPATH, '//a[@class=\"user-logined\" and @data-edrpou=\"' + edrpou + '\"]'))

    def clearCrtDocs(self):
        self.createdDocs = []
    def createNN(self):
        self.goTo('primarydocs')

        self._waitFor(self.VISIBILITY, (self.BY_CLASS_NAME, 'add-icon'))[1].click()
        self._waitFor(self.VISIBILITY, (self.BY_ID, 'taxBill'))[1].click()
        err, _ = self._waitFor(self.TITLE_CONTAIN, ('J1201008 - СОТА'))
        if err:
            self._logging("Can't create NN, traceback: "  + err)
        else:
            self._logging("NN is created successfully!")
    def createRK(self, type_ = 'minus'):
        self.goTo('prymarydocs')

        self._waitFor(self.VISIBILITY, (self.BY_CLASS_NAME, 'add-icon'))[1].click()
        self._waitFor(self.VISIBILITY, (self.BY_ID, 'addition'))[1].click()
        err, _ = self._waitFor(self.TITLE_CONTAIN, ('J1201208 - СОТА'))
        if err:
            self._logging("Can't create RK to NN, traceback: "  + err)
        else:
            self._logging("RK to NN is created successfully!")

    def copyOpenDoc(self, doc_type = 'primarydocs', cardcode = None):
        if cardcode:
            self._openDoc(cardcode,submenu=doc_type)
        self._slp(1)
        #get charcode
        err , _ = self._waitFor(self.TITLE_CONTAIN, ('J1201008'))
        if err:
            self._logging("Doc is not copied, traceback: {0}".format(err))
            return False
        charcode = self._getCharcodeOfDoc()
        err, element = self._waitFor(self.VISIBILITY, (self.BY_CLASS_NAME, 'copy-icon'))
        element.click()
        if doc_type == 'primarydocs':
            self._waitFor(self.VISIBILITY, (self.BY_ID, 'copyNaklWindow'))
        self.driver.find_element_by_class_name('ok-button').click()
        err , _ = self._waitFor(self.TITLE_CONTAIN, (charcode))
        if err:
            self._logging("Doc is not copied, charcode: {1},  traceback: {0}".format(err, charcode))
            return False
        self._logging('Doc with cardcode: {0}, and charcode: {1} is copied'.format(cardcode, charcode))
        return True

    def sendNNToPartner(self, cardcode=None):
        if cardcode:
            self._openDoc(cardcode)
        if self._getDocStatus() != self.SIGNED:
            if not self._signDoc():
                self._logging("Can't sign NN, cardcode: {0}".format(cardcode))
        self._sendDoc()
    def sendRkToPartner(self, carcode = None):
        if not cardcode:
            pass
        pass