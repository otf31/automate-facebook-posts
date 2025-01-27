import re

import fs
import typer
from playwright.sync_api import Playwright, Error, Page, expect

from common_functions import print_panel
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
    except AssertionError:
        return False
    except Error as e:
        print_panel(f"Error: {e}", msg_type="error")

    return True


def navigate(page: Page, url: str) -> None:
    """
    Navigates to the given URL.
    The errors are handled by the caller function.
    :param page: The browser page instance.
    :param url: The URL to navigate to.
    """
    page.goto(url)


def exit_app() -> None:
    """
    Exit the Typer application.
    """
    raise typer.Exit()
