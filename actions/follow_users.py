from selenium import webdriver
import time
import os
from selenium.webdriver.common import action_chains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


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
        "press Enter here to continue to the feed or search page where you want to follow users..."
    )


def go_to_brand_page():
    """
    Navigate directly to a brand page.
    The user can either paste a full brand URL or just type the brand name/slug.
    """
    brand_input = input(
        "Enter a Poshmark brand page URL (e.g. https://poshmark.com/brand/Coach)\n"
        "or just the brand name/slug (e.g. Coach): "
    ).strip()

    if brand_input.startswith("http"):
        brand_url = brand_input
    else:
        # Best-effort brand slug creation; user can always paste full URL instead
        brand_slug = brand_input.replace(" ", "-")
        brand_url = f"https://poshmark.com/brand/{brand_slug}"

    driver.get(brand_url)
    time.sleep(2)
    print(f"Navigated to brand page: {brand_url}")


def load_follow_candidates():
    """
    Scroll the brand page to load more listings / sellers.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    max_scrolls = 20
    scroll_count = 0

    while scroll_count < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count += 1
        if new_height == last_height:
            print("Reached the bottom of the brand page while loading listings.")
            break
        last_height = new_height

    if scroll_count >= max_scrolls:
        print(f"Hit scroll limit of {max_scrolls} loads; stopping auto-scroll.")

    print("Initial scroll to load brand listings is complete.")
    print("If you want to manually scroll further, change filters, or adjust the view,")
    print("do that now in the browser on the brand page.")
    input(
        "When you see listings from the brand whose sellers you want to follow, "
        "press Enter here to start opening closets and following in batches..."
    )


def collect_seller_urls():
    """
    Collect closet URLs for sellers on the current brand page.
    We look for seller anchors like:
    <a data-et-name="seller" href="/closet/username" ...>
    """
    anchors = driver.find_elements(
        By.XPATH, "//a[@data-et-name='seller' and contains(@href, '/closet/')]"
    )
    urls = []
    for a in anchors:
        href = a.get_attribute("href")
        if href and "/closet/" in href:
            urls.append(href.split("?")[0])
    deduped = list(dict.fromkeys(urls))
    print(f"Found {len(deduped)} seller closet URLs on the brand page.")
    return deduped


def follow_users_in_batches():
    """
    From a brand page, open each seller's closet and click the Follow button.
    """
    seller_urls = collect_seller_urls()
    total = len(seller_urls)

    if total == 0:
        print("No seller links found on this brand page. Try scrolling or changing filters, then rerun the script.")
        return

    batch_size = 10
    pause_seconds = 45

    print(
        f"Will attempt to follow up to {total} users from this brand page, "
        f"in batches of {batch_size} with a {pause_seconds}-second pause between batches."
    )
    input("Press Enter to begin opening closets and following users...")

    followed = 0
    attempted = 0

    for idx, closet_url in enumerate(seller_urls, start=1):
        # After each batch of `batch_size` follows, pause for a bit
        if idx > 1 and (idx - 1) % batch_size == 0:
            batch_number = (idx - 1) // batch_size
            print(
                f"Completed batch {batch_number} of {batch_size} follows "
                f"(followed {followed} users so far)."
            )
            print(f"Pausing for {pause_seconds} seconds before continuing to the next batch...")
            time.sleep(pause_seconds)

        attempted += 1
        try:
            # Open closet in a new tab to keep brand page intact
            brand_handle = driver.current_window_handle
            driver.execute_script("window.open(arguments[0], '_blank');", closet_url)
            driver.switch_to.window(driver.window_handles[-1])

            # Try to find a Follow button in the closet
            try:
                # Preferred: explicit follow_user button
                try:
                    follow_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//*[@data-et-name='follow_user']")
                        )
                    )
                except TimeoutException:
                    # Fallback: any older-style follow button if present
                    follow_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//*[@data-et-name='follow']")
                        )
                    )

                actions.move_to_element(follow_button).perform()
                time.sleep(0.5)
                follow_button.click()
                followed += 1
                print(f"Followed {followed} users (attempted {attempted}).")
            except TimeoutException:
                print(f"No Follow button found in closet {closet_url}. You may already be following this user.")

        except Exception as e:
            print(f"Failed to follow from closet {closet_url}: {e}")
        finally:
            # Close closet tab and return to brand page
            try:
                driver.close()
            except Exception:
                pass
            try:
                driver.switch_to.window(brand_handle)
            except Exception:
                pass

    print(
        f"Finished following users: successfully followed {followed} users "
        f"out of {attempted} attempts."
    )


if __name__ == "__main__":
    try:
        posh_login()
        go_to_brand_page()
        load_follow_candidates()
        follow_users_in_batches()
    finally:
        input("Press Enter to close the browser...")
        try:
            driver.close()
        except Exception:
            pass  # Browser/session already gone (e.g. after Ctrl+C)

