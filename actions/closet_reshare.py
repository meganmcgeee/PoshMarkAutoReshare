from selenium import webdriver
import time
import os
from selenium.webdriver.common import action_chains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

driver = webdriver.Chrome()
actions = ActionChains(driver)


def PoshLogin():
    loginUrl = 'https://poshmark.com/login'
    driver.get(loginUrl)

    driver.implicitly_wait(2)

    driver.find_element(By.NAME, value="login_form[username_email]").clear()
    driver.find_element(By.NAME, value="login_form[password]").clear()

    username_or_email = driver.find_element(by=By.NAME, value="login_form[username_email]")
    password_input = driver.find_element(by=By.NAME, value="login_form[password]")

    poshmark_username = os.environ.get("POSHMARK_USERNAME")
    poshmark_password = os.environ.get("POSHMARK_PASSWORD")

    if not poshmark_username or not poshmark_password:
        raise RuntimeError(
            "Missing Poshmark credentials. Please set POSHMARK_USERNAME and "
            "POSHMARK_PASSWORD environment variables before running this script."
        )

    username_or_email.send_keys(poshmark_username)
    password_input.send_keys(poshmark_password)

    # Let you manually click Login and handle any MFA / SMS prompts
    print("Poshmark username and password filled in the browser.")
    print("Now, in the Chrome window:")
    print("- Click the Login button.")
    print("- Complete any SMS / verification prompts.")
    input("When you have successfully logged in and see your Poshmark account, "
          "press Enter here to continue...")


def load_all_listings():
    scroll_pause_time = 10
    # These elements go to your closet
    driver.find_element(By.XPATH, '//*[@id="app"]/header/nav[1]/div/ul/li[5]/div').click()
    driver.find_element(By.XPATH, '//*[@id="app"]/header/nav[1]/div/ul/li[5]/div/div[2]/div/ul/li[1]').click()

    try:
        time.sleep(.5)
        driver.find_element(By.XPATH, '//*[@id="content"]/div[2]/div/div[2]/div[1]/button').click()
        print("close pop-up")
    except:
        print(" didn't find pop-up of closet beta thing")

    # this element is to find the Available Items button and click it
    try:
        driver.find_element(
            By.XPATH,
            '//*[@id="content"]/div[1]/div/div[2]/div/div[2]/nav/div/div[9]/div/div[2]/ul/li[2]/div/label/div'
        ).click()
    except ElementClickInterceptedException:
        print("Could not automatically click the 'Available Items' filter.")
        print("Please click the 'Available Items' (or any filters you prefer) manually in the browser.")
        input("After you've set the filters the way you want, press Enter here to continue...")
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait for new content to load, TODO make this dynamic based on page response
        time.sleep(1.5)
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Give you a chance to manually load or adjust listings if needed
    print("Initial scroll through your closet is complete.")
    print("If you want to manually scroll, change filters, or load more listings,")
    print("do that now in the browser.")
    input("When all the listings you want to share are visible, press Enter here to start sharing...")


def share_to_followers(share_btn):
    actions.move_to_element(share_btn).perform()
    try:
        time.sleep(.7)
        share_btn.click()
        to_my_followers = driver.find_element(By.CLASS_NAME, "share-wrapper-container")
        to_my_followers.click()
    except Exception as e:
        print(f"captcha block {e}")
    time.sleep(.2)


def share_listings(share_buttons):
    print("There are: ", len(share_buttons), " listings")
    i = 0
    for share_btn in share_buttons:
        share_to_followers(share_btn)
        i += 1
        print("Shared Listing: #", i)


if __name__ == '__main__':
    try:
        PoshLogin()
        load_all_listings()
        share_buttons = driver.find_elements(By.XPATH, '//div[@data-et-name="share"]')
        share_listings(share_buttons)
    finally:
        # Keep the browser open so you can see what happened
        input("Press Enter to close the browser...")
        driver.close()

