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
from rich.progress import track
from selenium.common import WebDriverException, NoSuchElementException, \
    ElementClickInterceptedException, NoSuchWindowException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

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
        chrome_options.add_experimental_option("detach", True)

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

        # Set the implicit wait
        driver.implicitly_wait(5)

        return driver
    except WebDriverException as e:
        print_panel(
            "[red]Error[/red]: %s" % e.msg,
            "error"
        )
        exit_app()


# TODO: try-except
def is_logged_in(driver: webdriver.WebDriver):
    navigate(driver, facebook_url + "/groups/feed/")

    return "Groups | Facebook" in driver.title


def find_element(driver: webdriver.WebDriver, by: By, value: str):
    element = driver.find_element(by, value)

    return element


def navigate(driver: webdriver.WebDriver, url: str):
    try:
        driver.get(url)
        sleep(5)
    except NoSuchWindowException as e:
        print_panel(f"Error: {e.msg}", "error")


def exit_app():
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


def validate_path(path: Path, path_type: str):
    if not path.exists():
        print_panel(f"Path {path} does not exist", "error")
    elif path_type == "file":
        if not path.is_file():
            print_panel(f"{path} is not a file", "error")
        elif path.stat().st_size == 0:
            print_panel(f"File {path} is empty", "error")
    elif path_type == "dir":
        if not path.is_dir():
            print_panel(f"{path} is not a directory", "error")
        elif not list(path.iterdir()):
            print_panel(f"Directory {path} is empty", "error")


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
        exit_app()

    input("Please login manually into your Facebook account, once you are logged in "
          "press ENTER...")

    exit_app()


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
    Publish posts (This command ignore headless option)
    """
    # Force no headless mode
    ctx.obj["headless"] = False

    posts_folder_path = Path(ctx.obj["posts_folder_path"])
    post_path = posts_folder_path / post
    post_images_path = post_path / "images"
    filters_path = post_path / "filters.txt"
    groups_file_path = posts_folder_path / "groups.csv"
    description_file_path = post_path / "description.txt"

    # Validate images folder
    validate_path(post_images_path, "dir")

    # Validate groups file
    validate_path(groups_file_path, "file")

    # Validate description file
    validate_path(description_file_path, "file")

    # Validate filters file
    validate_path(filters_path, "file")

    images_exts = [".jpg", ".jpeg", ".png"]

    # Images
    images = [image for image in post_images_path.iterdir() if
              image.suffix in images_exts]
    print_panel(f"Found {len(images)} images")

    # Description
    description: str
    with open(description_file_path, "r") as description_file:
        description = description_file.read().strip()

    print_panel(description)

    # Filters
    publication_filters: list[str]
    with open(filters_path, "r") as filters_file:
        text = filters_file.read()
        publication_filters = [f.strip().lower() for f in text.split(",")]

    print_panel(f"Filters: {publication_filters}")

    driver = init_driver(ctx)

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
        groups = []

        for row in rows:
            group_filters = [gf.strip().lower() for gf in row[2].split(",")]

            if len(set(publication_filters).intersection(set(group_filters))) > 0:
                groups.append(row)

        num_groups = len(groups)

        print_panel(f"This post is going to be publish in {num_groups} groups")

        for group in track(groups, "Publishing..."):
            try:
                group_name = group[0]
                group_url = group[1]

                print_panel(f"{group_name} - {group_url}")

                try:
                    # Navigate to the group
                    navigate(driver, group_url)

                    if "| Facebook" not in driver.title:
                        print_panel(
                            f"Group {group_name} does not exist or is not available",
                            "warning")
                        continue

                    try:
                        write_something = find_element(
                            driver,
                            By.XPATH,
                            "//span[contains(text(), 'Write something')]")
                        write_something.click()
                    except NoSuchElementException:
                        try:
                            start_discussion = find_element(
                                driver,
                                By.XPATH,
                                "//span[contains(text(), 'Start discussion')]")
                            start_discussion.click()
                        except NoSuchElementException:
                            # Go to Discussion tab
                            discussion_tab = find_element(
                                driver,
                                By.CSS_SELECTOR,
                                "a[href*='buy_sell_discussion']")
                            discussion_tab.click()

                            try:
                                write_something = find_element(
                                    driver,
                                    By.XPATH,
                                    "//span[contains(text(), 'Write something')]")
                                write_something.click()
                            except NoSuchElementException:
                                # Otherwise find the Start Discussion element
                                start_discussion = find_element(
                                    driver,
                                    By.XPATH,
                                    "//span[contains(text(), 'Start discussion')]")
                                start_discussion.click()

                    sleep(2)
                    textarea = driver.switch_to.active_element

                    # Copy the description to the clipboard
                    pyperclip.copy(description)
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
                    files = "\n".join([i.absolute().as_posix() for i in images])
                    sleep(1)
                    file_input.send_keys(files)
                    sleep(2)

                    # Press the Post button
                    post_button = find_element(
                        driver,
                        By.XPATH,
                        "//span[text()='Post']")
                    post_button.click()

                    print_panel(f"The post has been submitted to {group_name}")

                    posting_el = find_element(
                        driver,
                        By.XPATH,
                        "//span[contains(text(), 'Posting')]")

                    # Explicit wait until the posting text is not displayed
                    wait = WebDriverWait(driver, 15)
                    sleep(1)
                    wait.until(
                        ec.invisibility_of_element_located(posting_el))

                    sleep(1)
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
                # Catch any exception
                except Exception as e:
                    groups_with_errors.append((group_name, group_url, str(e)))
                    continue
            except IndexError as e:
                print_panel(f"{e}", "warning")
                continue

    print_panel("The task has been completed")

    if groups_with_errors:
        print_panel("Groups with errors", "warning")
        for group in groups_with_errors:
            print_panel(f"{group[0]} - {group[1]} - {group[2]}", "warning")

    # Write to a file log
    # publication timestamp groups without_errors with_errors
    with_errors = len(groups_with_errors)
    without_errors = num_groups - with_errors
    line = [post, datetime.now(), num_groups, without_errors, with_errors]

    with open(posts_folder_path / "log.csv", "a") as log_file:
        writer = csv.writer(log_file, delimiter=";")
        writer.writerow(line)

    exit_app()


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
            "chrome_profile": chrome_profile,
            "posts_folder_path": posts_folder_path
        }

    pass


if __name__ == "__main__":
    app()
