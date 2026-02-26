from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import unittest
import time


class RegisteringSeleniumTest(unittest.TestCase):


    def setUp(self):
        # Set up the Chrome driver (you can change to Firefox if you want)
        self.driver = webdriver.Chrome() # Make sure chromedriver is in PATH
        self.driver.implicitly_wait(10) # Implicit wait

    def tearDown(self):
        self.driver.quit()


    def test_registering(self):
        driver = self.driver
