import time
import pytest # type: ignore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("--headless")  # Remove this if you want to see the browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def test_user_can_login(driver):
    driver.get("http://localhost:3000/")

    # Fill username
    username_input = driver.find_element(By.ID, "username")
    username_input.send_keys("test_user_1")

    # Fill password
    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys("testpassword123")

    # Submit the form
    password_input.send_keys(Keys.RETURN)

    # Allow time for redirect
    time.sleep(2)

    # Confirm redirect or token set (optional DOM verification)
    assert "chat-rooms" in driver.current_url or "token" in driver.execute_script(
        "return localStorage.getItem('token');"
    )
