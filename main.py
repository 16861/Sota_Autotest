#main class

from selenium import webdriver
from selenium.webdriver.chrome import service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as excepts

from time import sleep
from datetime import datetime
import random, re, traceback

class AutotestMain:
    def __init__(self, page=None, browser = 'chrome', dev = True):
        self._site = page
        self._browser = browser
        if browser == "chrome":
            self.driver = webdriver.Chrome('/home/espadon/programming/Sota_Autotest/1/WebDrivers/chromedriver')
        elif browser == "firefox":
            self.driver = webdriver.Firefox()
        elif browser == "opera":
            webdriver_service = service.Service('C:\\operadriver32.exe')
            webdriver_service.start()
        elif browser == 'IE':
            self.driver = webdriver.Chrome('C:\\IEDriverServer32.exe')

            
        self.driver.set_page_load_timeout(20)
        if page:
            self.driver.get(page)

        #create log file
        with open('log.lg', 'w') as fd:
            pass


        self._logging("Starting webdriver...")

  
        self.VISIBILITY = 1
        self.PRESENCE = 2
        self.TITLE_CONTAIN = 3

        self.BY_CLASS_NAME = By.CLASS_NAME
        self.BY_ID = By.ID
        self.BY_XPATH = By.XPATH
        self.BY_CSS_SELECTOR = By.CSS_SELECTOR

        self.KEY_RETURN = Keys.RETURN

        self.ERROR = True
        self.DONE = False

        self.WebDriverException = excepts.WebDriverException

    def _error_handle(func):
        def _wrapper(self, *args):
            try:
                print("Args: ", *args)
                ret = func(self, *args)
                return None, ret
            except excepts.TimeoutException:
                print("Timeout exception encounter!")
                return traceback.format_exc() + " in fucntion: " + func.__name__, None 
            except excepts.WebDriverException:
                print("WebDriverException exception happened")
                return traceback.format_exc() + " in fucntion: " + func.__name__, None 
            except:
                return traceback.format_exc() + " in fucntion: " + func.__name__, None

        return _wrapper   


    
    def _closePopUp(self):
        try:
            WebDriverWait(self.driver, 5).until(
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
        
    def _getRandomDate(self):
        def twoDigit(x):
            if len(x) == 1:
                return '0' + x
            return x
    
        day = twoDigit(str(random.randint(1, 31)))
        mon = twoDigit(str(random.randint(1, 12)))
        # year = '2015'
        
        return day + mon + '2015'
    def _openPage(self, site):
        self.driver.get(site)
    @_error_handle
    def _waitFor(self, cond, route, time=2):
        if cond == self.VISIBILITY:
            return WebDriverWait(self.driver, time).until(
                EC.visibility_of_element_located(route)
            )
        elif cond == self.PRESENCE:
            return WebDriverWait(self.driver, time).until(
                EC.presence_of_element_located(route)
            )
        elif cond == self.TITLE_CONTAIN:
            return WebDriverWait(self.driver, time).until(
                EC.title_contains(route)
            )
    def _slp(self, time_=1):
        sleep(time_)
    def _errorLog(self, func, *args):
        try:
            if args:
                func(args[0])
            else:
                func()
            self._logging('Execution of function {0} ended successfully!'.format(func.__name__))
        except:
            self._logging('Error while executing function: {0}'.format(func.__name__))
            self._logging(traceback.format_exc())
            self.driver.close()
            exit(1)
    def getSessionID(self):
        return self.driver.session_id
    def getLocalStorage(self):
        ret = self.driver.execute_script("r = {}; for (var i = 0; i < localStorage.length; i++){key=localStorage.key(i); r[key] = localStorage.getItem(key);}; return r")
        return ret

    def closeDriver(self):
        self.driver.close()
        exit(0)

