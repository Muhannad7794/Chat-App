# chat-service/test/E2E_test/test_send_message_e2e.py

import time
import pytest  # type: ignore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


@pytest.fixture(scope="module")
def chrome_driver():
    options = Options()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def test_send_message(chrome_driver):
    chrome_driver.get("http://localhost:3000/")

    # Wait for the page to load
    time.sleep(2)

    # STEP 1: Log in
    username_input = chrome_driver.find_element(By.ID, "username")
    password_input = chrome_driver.find_element(By.ID, "password")
    login_button = chrome_driver.find_element(By.ID, "login-button")

    username_input.send_keys("test_user_1")
    password_input.send_keys("test_user_1_pwd")
    login_button.click()

    time.sleep(2)  # wait for navigation

    # STEP 2: Navigate to chat room (simulate if direct link is allowed)
    chrome_driver.get("http://localhost:3000/chat/43")  # Room ID 43 as example

    # STEP 3: Send a message
    message_input = chrome_driver.find_element(By.ID, "newMessage")
    message_input.send_keys("Hello from Selenium!" + Keys.RETURN)

    time.sleep(2)

    # STEP 4: Verify message appears
    messages = chrome_driver.find_elements(By.TAG_NAME, "p")
    assert any("Hello from Selenium!" in m.text for m in messages)
