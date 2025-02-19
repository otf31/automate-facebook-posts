import re

from playwright.async_api import Error, Page, expect

from constants import FACEBOOK_URL


async def is_logged_in(page: Page) -> bool:
    """
    Check if the user is logged in.
    :param page: The browser page instance.
    :return: A boolean indicating if the user is logged in.
    :raise AssertionError: If the user is not logged in.
    :raise playwright.sync_api.Error: If an error occurs during the process.
    """
    try:
        await navigate(page, FACEBOOK_URL + "/groups/feed/")

        await expect(page).to_have_title(re.compile(r".*Groups \| Facebook"))
    except AssertionError:
        return False
    except Error:
        return False
    else:
        return True


async def navigate(page: Page, url: str) -> None:
    """
    Navigates to the given URL.
    The errors are handled by the caller function.
    :param page: The browser page instance.
    :param url: The URL to navigate to.
    """
    await page.goto(url)
