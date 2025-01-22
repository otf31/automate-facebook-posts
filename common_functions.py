import random
import re
from time import sleep
from typing import Literal, Any

import fs
import machineid
import typer
from fs import open_fs
from fs.opener.errors import OpenerError
from playwright.sync_api import Playwright, Error, Page, expect
from rich import print
from rich.panel import Panel

from constants import FACEBOOK_URL


def launch_browser(
        ctx: typer.Context,
        p: Playwright
) -> Page:
    """
    Launch the browser.
    :param ctx: The Typer context.
    :param p: The Playwright instance.
    :return: A browser page.
    """
    chrome_binary_path = ctx.obj["chrome_binary_path"]
    headless = ctx.obj["headless"]
    posts_folder_path = ctx.obj["posts_folder_path"]
    chrome_data_dir = fs.path.combine(posts_folder_path, "/profile")

    try:
        browser = p.chromium.launch_persistent_context(
            executable_path=chrome_binary_path,
            user_data_dir=chrome_data_dir,
            headless=headless
        )

        page = browser.pages[0]

        return page
    except Error as e:
        print_panel(f"Error: {e}", msg_type="error")


def is_logged_in(page: Page) -> bool:
    """
    Check if the user is logged in.
    :param page: The browser page instance.
    :return: A boolean indicating if the user is logged in.
    :raise AssertionError: If the user is not logged in.
    :raise playwright.sync_api.Error: If an error occurs during the process.
    """
    try:
        navigate(page, FACEBOOK_URL + "/groups/feed/")

        expect(page).to_have_title(re.compile(r".*Groups \| Facebook"))

        return True
    except AssertionError:
        return False
    except Error as e:
        print_panel(f"Error: {e}", msg_type="error")


def navigate(page: Page, url: str) -> None:
    """
    Navigates to the given URL.
    The errors are handled by the caller function.
    :param page: The browser page instance.
    :param url: The URL to navigate to.
    """
    page.goto(url)


def exit_app():
    """
    Exit the Typer application.
    """
    raise typer.Exit()


def print_panel(msg: Any, title=None, msg_type: str = "info") -> None:
    """
    Print a panel with a message and an optional title.
    :param msg: Message inside the panel.
    :param title: Optional panel title.
    :param msg_type: info, error, warning or success.
        If error, the application will exit.
    """
    panel = Panel(msg, title=title, expand=False)

    if msg_type == "error":
        panel.style = "red"
    elif msg_type == "warning":
        panel.style = "yellow"
    elif msg_type == "success":
        panel.style = "green"

    print(panel)

    if msg_type == "error":
        exit_app()


def validate_path(
        tail: str,
        type_: Literal["file", "dir"],
        min_files: int = None
) -> None:
    """
    Validate the existence of a file or directory.
    :param tail: Absolute path to the resource.
    :param type_: The type of the resource: file or dir.
    :param min_files: If the resource is a directory,
        the minimum number of files it must contain. Default is None.
    :raise fs.opener.errors.OpenerError: Opening a filesystem with an invalid path.
    """
    head, tail = fs.path.split(tail)
    tail_sty = f"[bold blue]{tail}[/]"
    type_sty = f"[blue]{type_}[/]"

    try:
        with open_fs(head) as root_fs:
            if not root_fs.exists(tail):
                print_panel(
                    f"Resource {tail_sty} of type {type_sty} does not exist in {head}",
                    msg_type="error"
                )

            if type_ == "file":
                if not root_fs.isfile(tail):
                    print_panel(f"{tail_sty} is not a file", msg_type="error")
                elif root_fs.getsize(tail) == 0:
                    print_panel(f"File {tail_sty} is empty", msg_type="error")
            elif type_ == "dir":
                if not root_fs.isdir(tail):
                    print_panel(f"{tail_sty} is not a directory", msg_type="error")
                elif not root_fs.listdir(tail):
                    print_panel(f"Folder {tail_sty} is empty", msg_type="error")
                elif min_files is not None and len(root_fs.listdir(tail)) < min_files:
                    print_panel(
                        f"Folder {tail_sty} must contain at least {min_files} files",
                        msg_type="error"
                    )
    except OpenerError:
        print_panel(f"Path {head} does not exist", msg_type="error")


def wait_random_seconds(start: int, end: int = None) -> None:
    """
    Wait a random time between start and end seconds.
    :param start: The start time in seconds
    :param end: The end time in seconds, if None, the end time will be equal to start time
    and the function will wait exactly the start time.
    """
    if end is None:
        end = start

    sleep(random.randint(start, end))


def get_device_id() -> str:
    """
    Get the device id.
    :return:
    """
    return machineid.hashed_id()
