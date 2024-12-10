import csv
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Annotated, Optional

import click
import pyperclip
import typer
from rich import print
from rich.panel import Panel
from selenium.common import WebDriverException, NoSuchElementException, \
    ElementClickInterceptedException, NoSuchWindowException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

app = typer.Typer(no_args_is_help=True)

# Get HOME environment variable
home = Path.home()
facebook_url = "https://www.facebook.com"
chrome_binary_path_ = "/opt/google/chrome/google-chrome"
chrome_driver_path_ = "%s/Desktop/chromedriver/chromedriver-linux64/chromedriver" % home
chrome_config_path_ = "%s/.config/google-chrome" % home
chrome_profile_ = "Profile 3"
posts_folder_path_ = "%s/Desktop/publication" % home
available_posts = []


def init_driver(
        ctx: typer.Context
):
    print_panel("Initializing the driver...")
    chrome_binary_path = ctx.obj["chrome_binary_path"]
    chrome_driver_path = ctx.obj["chrome_driver_path"]
    headless = ctx.obj["headless"]
    chrome_config_path = ctx.obj["chrome_config_path"]
    chrome_profile = ctx.obj["chrome_profile"]

    try:
        # Chrome options
        chrome_options = webdriver.Options()
        chrome_options.binary_location = chrome_binary_path
        chrome_options.add_argument("--remote-debugging-port=3322")
        chrome_options.add_argument("--disable-extensions")
        # chrome_options.add_experimental_option("detach", True)
        if headless:
            chrome_options.add_argument("--headless")

        if not Path(chrome_driver_path).exists():
            print_panel(f"Chrome driver path {chrome_driver_path} does not exist",
                        "error")

        if not Path(chrome_config_path).exists():
            print_panel(f"Chrome config path {chrome_config_path} does not exist",
                        "error")

        if not (Path(chrome_config_path) / chrome_profile).exists():
            print_panel(f"Chrome profile {chrome_profile} does not exist", "error")

        chrome_options.add_argument(f"--user-data-dir={chrome_config_path}")
        chrome_options.add_argument(f"--profile-directory={chrome_profile}")

        # Chrome service
        service = webdriver.Service(executable_path=chrome_driver_path)

        # Create the driver
        driver = webdriver.WebDriver(options=chrome_options, service=service)

        return driver
    except WebDriverException as e:
        print_panel(
            "[red]Error[/red]: %s" % e.msg,
            "error"
        )


def is_logged_in(driver: webdriver.WebDriver):
    sleep(1)
    navigate(driver, facebook_url + "/groups/feed/")

    return "Groups | Facebook" in driver.title


def find_element(driver: webdriver.WebDriver, by: By, value: str):
    element = driver.find_element(by, value)
    sleep(1)

    return element


def navigate(driver: webdriver.WebDriver, url: str):
    try:
        driver.get(url)
        sleep(5)
    except NoSuchWindowException as e:
        print_panel(f"Error: {e.msg}", "error")


def exit_app(driver):
    driver.quit()
    raise typer.Exit()


def print_panel(
        msg: str,
        msg_type: str = "info"
):
    panel = Panel(msg, expand=False)

    if msg_type == "error":
        panel.style = "red"
    elif msg_type == "warning":
        panel.style = "yellow"
    else:
        panel.style = "green"

    print(panel)

    if msg_type == "error":
        raise typer.Exit()


@app.command()
def login(
        ctx: typer.Context
):
    """
    Login into Facebook (this command ignore headless option)
    """
    # Force no headless mode
    ctx.obj["headless"] = False

    driver = init_driver(ctx)
    sleep(3)

    print_panel("Checking if the user is logged in...")
    if is_logged_in(driver):
        print_panel("You are already logged in", "warning")
        exit_app(driver)

    input("Please login manually into your Facebook account, once you are logged in "
          "press ENTER...")

    exit_app(driver)


@app.command()
def publish(
        ctx: typer.Context,
        post: Annotated[
            str,
            typer.Option(
                help="The post",
                prompt="Select a post",
                show_choices=True,
                click_type=click.Choice(available_posts)
            )
        ]
):
    """
    Publish posts
    """
    post_path = Path(posts_folder_path_) / post
    post_images_path = post_path / "images"

    # Check whether the images folder exists
    if not post_images_path.exists():
        print_panel(f"Images folder {post_images_path} does not exist", "error")
    else:
        # Check whether the images folder is a directory
        if not post_images_path.is_dir():
            print_panel(f"{post_images_path} is not a folder, it must be a directory",
                        "error")
        else:
            # Check whether the images folder is empty
            if not list(post_images_path.iterdir()):
                print_panel(f"Images folder {post_images_path} is empty", "error")

    # Check wheter the groups file exists (groups.csv)
    groups_file_path = post_path / "groups.csv"

    if not groups_file_path.exists():
        print_panel(f"Groups file {groups_file_path} does not exist", "error")
    else:
        # Check whether is a file
        if not groups_file_path.is_file():
            print_panel(f"{groups_file_path} is not a file", "error")
        else:
            # Check whether the groups file is empty
            if groups_file_path.stat().st_size == 0:
                print_panel(f"Groups file {groups_file_path} is empty", "error")

    # Check whether the description file exists (description.txt)
    description_file_path = post_path / "description.txt"

    if not description_file_path.exists():
        print_panel(f"Description file {description_file_path} does not exist", "error")
    else:
        # Check whether is a file
        if not description_file_path.is_file():
            print_panel(f"{description_file_path} is not a file", "error")
        else:
            # Check whether the description file is empty
            if description_file_path.stat().st_size == 0:
                print_panel(f"Description file {description_file_path} is empty", "error")

    images_exts = [".jpg", ".jpeg", ".png"]

    # Images
    images = [image for image in post_images_path.iterdir() if
              image.suffix in images_exts]
    print_panel(f"Found {len(images)} images")

    # Text
    description: str
    with open(description_file_path, "r") as description_file:
        description = description_file.read()

    print_panel(description)

    driver = init_driver(ctx)
    sleep(3)

    print_panel("Checking if the user is logged in...")
    if not is_logged_in(driver):
        print_panel(
            "You are not logged in, please sign in manually into your Facebook account "
            "using the [blue]login[/blue] command and be sure that you are with the "
            "right profile",
            "error")

    # Press ENTER to continue
    input("Press ENTER to continue the process...")

    groups_with_errors = []

    # Read the groups file
    with open(groups_file_path, "r") as groups_file:
        reader = csv.reader(groups_file, delimiter=";")
        rows = list(reader)
        num_groups = len(rows)

        print_panel(f"This post is going to be publish in {num_groups} groups")

        for row in rows:
            try:
                group_name = row[0]
                group_url = row[1]

                print_panel(f"Group: {group_name} - URL: {group_url}")

                # Navigate to the group with subpath /buy_sell_discussion
                navigate(driver, group_url + "buy_sell_discussion")

                if driver.title == "Facebook":
                    print_panel(f"Group {group_name} does not exist or is not available",
                                "warning")
                    continue

                try:
                    try:
                        # Find the Write something element
                        write_something_el = find_element(
                            driver,
                            By.XPATH,
                            "//span[contains(text(), 'Write something')]")
                        write_something_el.click()
                    except NoSuchElementException:
                        navigate(driver, group_url)

                        try:
                            # Otherwise find the Start Discussion element
                            start_discussion_el = find_element(
                                driver,
                                By.XPATH,
                                "//span[contains(text(), 'Start discussion')]")
                            start_discussion_el.click()
                        except NoSuchElementException:
                            write_something_el = find_element(
                                driver,
                                By.XPATH,
                                "//span[contains(text(), 'Write something')]")
                            write_something_el.click()

                    sleep(3)

                    try:
                        textarea = find_element(
                            driver, By.XPATH,
                            "//div[contains(@aria-label, 'Create a public post')]")
                    except NoSuchElementException:
                        textarea = find_element(
                            driver, By.XPATH,
                            "//div[contains(@aria-label, 'Write something')]")

                    # Copy the description to the clipboard
                    pyperclip.copy(description.strip())
                    sleep(1)

                    # Paste the description
                    textarea.send_keys(Keys.CONTROL + "v")
                    sleep(2)

                    # Find Photo/Video element and click it
                    photo_video_el = find_element(
                        driver,
                        By.CSS_SELECTOR,
                        '[aria-label="Photo/video"]')
                    photo_video_el.click()
                    sleep(1)

                    # Get the file input element
                    file_input = find_element(
                        driver,
                        By.CSS_SELECTOR,
                        '[accept="image/*,image/heif,image/heic,video/*,video/mp4,'
                        'video/x-m4v,video/x-matroska,.mkv"]')

                    # Upload the images
                    files = "\n".join([image.absolute().as_posix() for image in images])
                    file_input.send_keys(files)
                    sleep(3)

                    # Press the Post button
                    post_button = find_element(
                        driver,
                        By.XPATH,
                        "//span[text()='Post']")

                    post_button.click()
                    print_panel(f"The post has been submitted to the group {group_name}")
                    sleep(15)
                except NoSuchElementException as e:
                    groups_with_errors.append((group_name, group_url, e.msg))
                    continue
                except ElementClickInterceptedException as e:
                    groups_with_errors.append((group_name, group_url, e.msg))
                    continue
                # This is a general exception
                except WebDriverException as e:
                    groups_with_errors.append((group_name, group_url, e.msg))
                    continue
            except IndexError as e:
                print_panel(f"{e}", "warning")
                continue

    print_panel("The task has been completed")

    if groups_with_errors:
        print_panel("Groups with errors", "warning")
        for group in groups_with_errors:
            print_panel(f"Group: {group[0]} - URL: {group[1]} - {group[2]}", "warning")

    # Write to a file log
    # publication timestamp groups without_errors with_errors
    with_errors = len(groups_with_errors)
    without_errors = num_groups - with_errors
    line = [post, datetime.now(), num_groups, without_errors, with_errors]
    
    with open(post_path / "log.csv", "a") as log_file:
        writer = csv.writer(log_file, delimiter=";")
        writer.writerow(line)

    input("Press ENTER to finish the process...")


@app.callback()
def callback(
        ctx: typer.Context,
        chrome_binary_path: Annotated[
            Optional[str],
            typer.Option(
                help="The Chrome binary path"
            )
        ] = chrome_binary_path_,
        chrome_driver_path: Annotated[
            Optional[str],
            typer.Option(
                help="The Chrome driver path"
            )
        ] = chrome_driver_path_,
        chrome_config_path: Annotated[
            Optional[str],
            typer.Option(
                help="The Chrome config path"
            )
        ] = chrome_config_path_,
        chrome_profile: Annotated[
            Optional[str],
            typer.Option(
                help="The Chrome profile"
            )
        ] = chrome_profile_,
        headless: Annotated[
            Optional[bool],
            typer.Option(
                help="Run the browser in headless mode"
            )
        ] = False,
        posts_folder_path: Annotated[
            Optional[str],
            typer.Option(
                help="The folder containing the posts"
            )
        ] = posts_folder_path_
):
    """
    Automate facebook posts.
    """
    # Find available posts
    posts_folder = Path(posts_folder_path)

    if not posts_folder.exists():
        print_panel(f"Folder {posts_folder_path} does not exist", "error")
    else:
        for file in posts_folder.iterdir():
            if file.is_dir():
                available_posts.append(file.name)

        if not available_posts:
            print_panel(f"No posts found in {posts_folder_path}", "error")

        ctx.obj = {
            "chrome_binary_path": chrome_binary_path,
            "chrome_driver_path": chrome_driver_path,
            "headless": headless,
            "chrome_config_path": chrome_config_path,
            "chrome_profile": chrome_profile
        }

    pass


if __name__ == "__main__":
    app()
