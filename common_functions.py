import random
from pathlib import Path
from time import sleep

import typer
from playwright.sync_api import Playwright, Error, Page, expect
from rich import print
from rich.panel import Panel

from constants import CHROME_USER_DATA_DIR, FACEBOOK_URL


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
    
    try:
        browser = p.chromium.launch_persistent_context(
            executable_path=chrome_binary_path,
            user_data_dir=CHROME_USER_DATA_DIR,
            headless=headless
        )

        page = browser.pages[0]

        return page
    except Error as e:
        print_panel(f"Error: {e}", "error")


def is_logged_in(page: Page):
    try:
        navigate(page, FACEBOOK_URL + "/groups/feed/")

        expect(page).to_have_title("Groups | Facebook")

        return True
    except AssertionError:
        return False
    except Error as e:
        print_panel(f"Error: {e}", "error")


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
    elif msg_type == "success":
        panel.style = "green"

    print(panel)

    if msg_type == "error":
        raise typer.Exit()


def validate_path(path: Path, path_type: str, min_files: int = None):
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
        elif min_files is not None and len(list(path.iterdir())) < min_files:
            print_panel(
                f"Directory {path} must contain at least {min_files} files", "error"
            )


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
