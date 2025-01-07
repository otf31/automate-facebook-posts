import csv
import random
import re
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Annotated, Optional

import click
import typer
from playwright.sync_api import Playwright, Page, sync_playwright, Error, TimeoutError
from rich import print
from rich.panel import Panel
from rich.progress import track

app = typer.Typer(no_args_is_help=True)

# Get HOME environment variable
home = Path.home()
FACEBOOK_URL = "https://www.facebook.com"
CHROME_BINARY_PATH = "/opt/google/chrome/google-chrome"
POST_FOLDER_PATH = f"{home}/Desktop/publication"
CHROME_USER_DATA_DIR = f"{POST_FOLDER_PATH}/profile"
available_posts = []


def launch_browser(
        ctx: typer.Context,
        p: Playwright
):
    """
    Launch the browser.

    :param ctx: The Typer context.
    :param p: The Playwright instance.
    :return: A browser page.
    """
    chrome_binary_path = ctx.obj["chrome_binary_path"]
    headless = ctx.obj["headless"]

    print("[green]Launching browser...[/green]")

    try:
        browser = p.chromium.launch_persistent_context(
            executable_path=chrome_binary_path,
            user_data_dir=CHROME_USER_DATA_DIR,
            headless=headless,
            # args=["--profile-directory=%s" % chrome_profile]
        )
        page = browser.pages[0]

        return page
    except Error as e:
        print_panel(f"Error: {e}", "error")


# TODO: try-except
def is_logged_in(page: Page):
    navigate(page, FACEBOOK_URL + "/groups/feed/")

    return "Groups | Facebook" in page.title()


def navigate(page: Page, url: str):
    page.goto(url)


def exit_app():
    raise typer.Exit()


def print_panel(msg: str, msg_type: str = "info"):
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


def wait_random_seconds(start: int, end: int = None):
    """
    Wait a random time between start and end seconds.
    :param start: The start time in seconds
    :param end: The end time in seconds, if None, the end time will be equal to start time
    and the function will wait exactly the start time.
    """
    if end is None:
        end = start

    sleep(random.randint(start, end))


@app.command()
def test(ctx: typer.Context):
    """
    Test command
    """
    print("Test command")

    with sync_playwright() as p:
        page = launch_browser(ctx, p)
        navigate(page, "http://192.168.1.1")

        el = page.get_by_text(re.compile("Login."), exact=True)
        print(el)

        a = el.is_visible()

        if a:
            print("Visible")
        else:
            print("Not visible")

        input("Press ENTER to continue...")
        page.close()

    exit_app()


@app.command()
def login(ctx: typer.Context):
    """
    Login into Facebook (this command ignore headless option)
    """
    # Force headful mode
    ctx.obj["headless"] = False

    with sync_playwright() as p:
        page = launch_browser(ctx, p)

        if is_logged_in(page):
            print_panel("You are already logged in", "error")

        print_panel(
            "Please, [blue]login manually into your Facebook account[/blue]")
        input("Press ENTER once you are logged in...")

        page.close()


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
    # Force headful mode
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

    with sync_playwright() as p:
        page = launch_browser(ctx, p)

        print_panel("Checking if the user is logged in...")
        if not is_logged_in(page):
            print_panel(
                "You are not logged in, [blue]please sign in manually into your Facebook "
                "account[/blue] using the [blue]login[/blue] command and set your "
                "Facebook profile if necessary, then try again",
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

            print_panel(f"This post is going to be publish in {num_groups} groups, do "
                        f"not close the browser")

            for index, group in track(enumerate(groups), "Publishing..."):
                try:
                    group_name = group[0]
                    group_url = group[1]

                    print_panel(f"{group_name} - {group_url}")

                    try:
                        # Navigate to the group
                        navigate(page, group_url)

                        sleep(2)

                        if "| Facebook" not in page.title():
                            print_panel(
                                f"Group {group_name} does not exist or is not available",
                                "warning")
                            continue

                        write_something = page.get_by_role(
                            "button",
                            name=re.compile("Write something.*")
                        )

                        if write_something.is_visible():
                            write_something.click()
                        else:
                            start_discussion = page.get_by_role(
                                "button",
                                name=re.compile("Start discussion.*")
                            )

                            if start_discussion.is_visible():
                                start_discussion.click()
                            else:
                                # Go to Discussion tab
                                page.locator(
                                    "a[href*='buy_sell_discussion']").click()

                                page.wait_for_url(
                                    re.compile(".*/buy_sell_discussion"))

                                sleep(2)

                                write_something = page.get_by_role(
                                    "button",
                                    name=re.compile("Write something.*"))

                                if write_something.is_visible():
                                    write_something.click()
                                else:
                                    start_discussion = page.get_by_role(
                                        "button",
                                        name=re.compile("Start discussion.*"))

                                    if start_discussion.is_visible():
                                        start_discussion.click()
                                    else:
                                        groups_with_errors.append(
                                            (group_name, group_url,
                                             "Cannot find any way to post"))

                                        continue

                        post_button = page.get_by_text("Post", exact=True)
                        post_button.wait_for()

                        textarea = page.locator('*:focus')

                        # Fill the description
                        textarea.fill(description)

                        # Find Photo/Video element and click it
                        photo_video_el = page.locator('[aria-label="Photo/video"]')

                        photo_video_el.click()

                        # Get the file input element
                        file_input = page.locator(
                            '[accept="image/*,image/heif,image/heic,video/*,video/mp4,'
                            'video/x-m4v,video/x-matroska,.mkv"]')

                        # Upload the images
                        files = [i.absolute().as_posix() for i in images]
                        file_input.set_input_files(files)

                        sleep(2)

                        # Press the Post button
                        post_button.click()

                        print_panel(f"The post has been submitted to {group_name}")

                        # Posting element
                        posting_el = page.get_by_text(re.compile("Posting.*"))

                        # Wait until the posting text is detached
                        posting_el.wait_for(state="detached")

                        # Wait a random time between 1 and 2 minutes
                        if (index + 1) % 5 == 0:
                            wait_random_seconds(60 * 1, 60 * 2)
                        # Wait a random time between 25 and 45 seconds
                        else:
                            wait_random_seconds(25, 45)
                    except TimeoutError as e:
                        groups_with_errors.append((group_name, group_url, e.message))
                        continue
                    # Playwright Error
                    except Error as e:
                        groups_with_errors.append((group_name, group_url, e.message))
                        continue
                    # Any exception
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
        ] = CHROME_BINARY_PATH,
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
        ] = POST_FOLDER_PATH
):
    """
    Automate facebook posts.
    """
    posts_folder = Path(posts_folder_path)

    # Check if the profile folder exists
    profile_folder = Path(posts_folder) / "profile"

    # If not exists, create it
    if not profile_folder.exists():
        profile_folder.mkdir()

    # Find available posts
    if not posts_folder.exists():
        print_panel(f"Folder {posts_folder_path} does not exist", "error")
    else:
        for file in posts_folder.iterdir():
            if file.is_dir() and file.name != "profile":
                available_posts.append(file.name)

        if not available_posts:
            print_panel(f"No posts found in {posts_folder_path}", "error")

        ctx.obj = {
            "chrome_binary_path": chrome_binary_path,
            "headless": headless,
            "posts_folder_path": posts_folder_path
        }

    pass


if __name__ == "__main__":
    app()
