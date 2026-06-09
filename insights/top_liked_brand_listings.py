import os
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


driver = webdriver.Chrome()


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
        "press Enter here to continue to the brand page..."
    )


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


def load_brand_listings():
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

    print("If you want to manually scroll or adjust filters,")
    print("do that now in the browser on the brand page.")
    input(
        "When you are ready to analyze the visible listings for likes, "
        "press Enter here to continue..."
    )


def parse_like_count(text: str) -> int:
    """
    Best-effort parsing of a like count from a text snippet.
    """
    if not text:
        return 0
    match = re.search(r"\d+", text.replace(",", ""))
    if not match:
        return 0
    try:
        return int(match.group(0))
    except ValueError:
        return 0


def collect_listing_like_data():
    """
    Collect listing URLs and their like counts from the brand page.
    This is best-effort and relies on heuristics to find the likes text.
    """
    anchors = driver.find_elements(By.XPATH, '//a[contains(@href, "/listing/")]')
    seen_urls = set()
    listing_data = []

    for a in anchors:
        href = a.get_attribute("href")
        if not href or "/listing/" not in href:
            continue
        url = href.split("?", 1)[0]
        if url in seen_urls:
            continue
        seen_urls.add(url)

        likes = 0
        # Try to find a nearby element that looks like a likes counter
        try:
            container = a.find_element(
                By.XPATH,
                "./ancestor::div[contains(@class,'tile') or contains(@class,'card')][1]",
            )
        except Exception:
            container = None

        candidates = []
        if container is not None:
            try:
                candidates = container.find_elements(
                    By.XPATH,
                    ".//*[contains(@class,'like') or contains(@class,'likes') or "
                    "contains(translate(text(),'LIKES','likes'),'likes')]",
                )
            except Exception:
                candidates = []

        for c in candidates:
            likes = max(likes, parse_like_count(c.text))

        listing_data.append({"url": url, "likes": likes})

    print(f"Collected like data for {len(listing_data)} listings.")
    return listing_data


def show_top_liked():
    listing_data = collect_listing_like_data()
    if not listing_data:
        print("No listings found to analyze.")
        return

    try:
        top_n_input = input(
            "How many top listings do you want to see? (default 20): "
        ).strip()
        top_n = int(top_n_input) if top_n_input else 20
    except ValueError:
        top_n = 20

    # Sort by likes descending, then by URL for stability
    listing_data.sort(key=lambda x: (x["likes"], x["url"]), reverse=True)
    top = listing_data[:top_n]

    print(f"\nTop {len(top)} listings by likes on this brand page:\n")
    for idx, item in enumerate(top, start=1):
        print(f"{idx}. {item['likes']} likes\t{item['url']}")
        
    import json
    # Save the output to a JSON file in the project root
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "insights.json")
    try:
        with open(output_path, "w") as f:
            json.dump(top, f, indent=2)
    except Exception as e:
        print(f"Failed to save insights to JSON: {e}")


if __name__ == "__main__":
    try:
        posh_login()
        go_to_brand_page()
        load_brand_listings()
        show_top_liked()
    finally:
        input("\nAnalysis complete. Press Enter to close the browser...")
        try:
            driver.close()
        except Exception:
            pass

