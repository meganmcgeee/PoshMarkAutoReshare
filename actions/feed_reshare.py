from selenium import webdriver
import time
import os
from selenium.webdriver.common import action_chains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException

driver = webdriver.Chrome()
actions = ActionChains(driver)


def posh_login():
    login_url = "https://poshmark.com/login"
    driver.get(login_url)

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

    print("Poshmark username and password filled in the browser.")
    print("Now, in the Chrome window:")
    print("- Click the Login button.")
    print("- Complete any SMS / verification prompts.")
    input(
        "When you have successfully logged in and see your Poshmark account, "
        "press Enter here to continue..."
    )


def ask_share_source():
    """Return 'feed', 'brand', or 'user'."""
    print("Where do you want to share listings from?")
    print("  1 = Your main feed")
    print("  2 = A brand page")
    print("  3 = A user's closet")
    while True:
        choice = input("Enter 1, 2, or 3: ").strip()
        if choice == "1":
            return "feed"
        if choice == "2":
            return "brand"
        if choice == "3":
            return "user"
        print("Please enter 1, 2, or 3.")


def go_to_feed():
    driver.get("https://poshmark.com/feed")
    time.sleep(2)
    print("Navigated to your Poshmark feed.")


def go_to_brand_page():
    brand_input = input(
        "Enter a Poshmark brand page URL (e.g. https://poshmark.com/brand/Coach)\n"
        "or just the brand name/slug (e.g. Coach): "
    ).strip()
    if brand_input.startswith("http"):
        brand_url = brand_input
    else:
        brand_slug = brand_input.replace(" ", "-")
        brand_url = f"https://poshmark.com/brand/{brand_slug}"
    driver.get(brand_url)
    time.sleep(2)
    print(f"Navigated to brand page: {brand_url}")


def go_to_user_closet():
    user_input = input(
        "Enter a Poshmark closet URL (e.g. https://poshmark.com/closet/username)\n"
        "or just the username: "
    ).strip()
    if user_input.startswith("http"):
        closet_url = user_input.split("?")[0]
    else:
        username = user_input.strip().lstrip("@")
        closet_url = f"https://poshmark.com/closet/{username}"
    driver.get(closet_url)
    time.sleep(2)
    print(f"Navigated to closet: {closet_url}")


def load_listings(source):
    """Scroll to load listings. For brand/user, cap scrolls to avoid getting stuck."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    max_scrolls = None if source == "feed" else 20
    scroll_count = 0

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count += 1
        if new_height == last_height:
            if source != "feed":
                print("Reached the bottom of the page.")
            break
        last_height = new_height
        if max_scrolls is not None and scroll_count >= max_scrolls:
            print(f"Hit scroll limit of {max_scrolls}; stopping.")
            break

    print("Initial scroll is complete.")
    print("If you want to manually scroll further or change filters, do that now in the browser.")
    input(
        "When all the listings you want to share are visible, "
        "press Enter here to start sharing..."
    )


def share_to_followers(share_btn):
    actions.move_to_element(share_btn).perform()
    try:
        time.sleep(0.7)
        share_btn.click()
        to_my_followers = driver.find_element(By.CLASS_NAME, "share-wrapper-container")
        to_my_followers.click()
    except Exception as e:
        print(f"captcha or share block: {e}")
    time.sleep(0.2)


def collect_feed_listing_urls():
    anchors = driver.find_elements(By.XPATH, '//a[contains(@href, "/listing/")]')
    urls = []
    for a in anchors:
        href = a.get_attribute("href")
        if href and "/listing/" in href:
            urls.append(href.split("?")[0])
    deduped = list(dict.fromkeys(urls))
    print("Found", len(deduped), "listing URLs on this page.")
    return deduped


def share_listing_url(url):
    # Open listing in a new tab so we don't lose the feed scroll position
    feed_handle = driver.current_window_handle
    driver.execute_script("window.open(arguments[0], '_blank');", url)
    driver.switch_to.window(driver.window_handles[-1])

    try:
        try:
            # Preferred: Share button on the listing details section
            share_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//div[@data-et-name="share" and @data-et-prop-location="listing_details"]',
                    )
                )
            )
        except TimeoutException:
            # Fallback: any on-page share button if the specific one is missing
            print("Listing-details Share button not found, trying any on-page share button...")
            share_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//div[@data-et-name="share"]')
                )
            )

        share_to_followers(share_button)
        return True
    except TimeoutException:
        print("Could not find a Share button on listing page for:", url)
        print("If the listing page looks different, share it manually, then press Enter to continue.")
        input("Press Enter to continue...")
        return False
    finally:
        # Close listing tab and return to feed
        try:
            driver.close()
        except Exception:
            pass
        try:
            driver.switch_to.window(feed_handle)
        except Exception:
            pass


def share_feed_listings():
    listing_urls = collect_feed_listing_urls()
    total_found = len(listing_urls)
    print(f"Found {total_found} listing URLs on this page.")
    print("Will share in batches of up to 10 listings,")
    print("pausing for 45 seconds between batches to avoid rate limits.")
    input("Press Enter to begin opening each listing and sharing it...")

    shared = 0
    attempted = 0
    batch_size = 10
    for idx, url in enumerate(listing_urls, start=1):
        # After each batch of 10 listings, pause for 45 seconds
        if idx > 1 and (idx - 1) % batch_size == 0:
            batch_number = (idx - 1) // batch_size
            print(
                f"Completed batch {batch_number} of {batch_size} listings "
                f"(shared {shared} so far)."
            )
            print("Pausing for 45 seconds before continuing to the next batch...")
            time.sleep(45)

        attempted += 1
        ok = share_listing_url(url)
        if ok:
            shared += 1
            print("Shared", shared, "of", attempted)
        else:
            print("Skipped/Manual for", attempted, "of", len(listing_urls))

    print(
        f"Finished all batches after sharing {shared} listings "
        f"(attempted {attempted})."
    )


if __name__ == "__main__":
    try:
        posh_login()
        source = ask_share_source()
        if source == "feed":
            go_to_feed()
        elif source == "brand":
            go_to_brand_page()
        else:
            go_to_user_closet()
        load_listings(source)
        share_feed_listings()
    finally:
        input("Press Enter to close the browser...")
        try:
            driver.close()
        except Exception:
            pass  # Browser/session already gone (e.g. after Ctrl+C)


