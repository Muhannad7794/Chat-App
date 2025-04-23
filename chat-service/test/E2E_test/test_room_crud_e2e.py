# chat-service/test/E2E_test/test_room_crud_e2e.py

import time
import pytest  # type: ignore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("--headless")  # Remove to view browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def test_room_crud_e2e(driver):
    base_url = "http://localhost:3000"
    driver.get(base_url)
    time.sleep(2)

    # -- LOGIN PAGE (if applicable) --
    # driver.find_element(By.ID, "username").send_keys("test_user_1")
    # driver.find_element(By.ID, "password").send_keys("test_password")
    # driver.find_element(By.ID, "login-button").click()
    # time.sleep(2)

    # -- CREATE CHAT ROOM --
    driver.find_element(By.XPATH, "//button[text()='Create Chat Room']").click()
    time.sleep(1)

    room_name = "SeleniumRoom"
    members = "test_user_2"

    driver.find_element(By.XPATH, "//input[@placeholder='Enter room name']").send_keys(
        room_name
    )
    driver.find_element(
        By.XPATH, "//input[@placeholder='Username1, Username2']"
    ).send_keys(members)
    driver.find_element(By.XPATH, "//button[text()='Create Room']").click()

    time.sleep(2)
    assert room_name in driver.page_source, "Room was not created"

    # -- RENAME CHAT ROOM --
    driver.find_element(
        By.XPATH, f"//div[text()='{room_name}']/../../div/button[text()='Rename']"
    ).click()
    time.sleep(1)
    new_name = "RenamedRoom"
    rename_input = driver.find_element(
        By.XPATH, "//input[@placeholder='Enter new room name']"
    )
    rename_input.clear()
    rename_input.send_keys(new_name)
    driver.find_element(By.XPATH, "//button[text()='Rename']").click()

    time.sleep(2)
    assert new_name in driver.page_source, "Room was not renamed"

    # -- DELETE CHAT ROOM --
    driver.find_element(
        By.XPATH, f"//div[text()='{new_name}']/../../div/button[text()='Delete']"
    ).click()
    time.sleep(1)
    driver.find_element(By.XPATH, "//button[text()='Delete']").click()

    time.sleep(2)
    assert new_name not in driver.page_source, "Room was not deleted"
