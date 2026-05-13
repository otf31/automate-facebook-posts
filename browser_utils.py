import re

from playwright.async_api import Error, Page, expect

from constants import FACEBOOK_URL, SUPPORTED_FB_LANGUAGES


async def is_logged_in(page: Page, expected_title_pattern: str) -> bool:
    """
    Check if the user is logged in.
    :param page: The browser page instance.
    :param expected_title_pattern: The expected title of the Facebook groups page.
    :return: A boolean indicating if the user is logged in.
    :raise AssertionError: If the user is not logged in.
    :raise playwright.sync_api.Error: If an error occurs during the process.
    """

    try:
        await expect(page).to_have_title(re.compile(expected_title_pattern))
    except AssertionError:
        return False
    except Error:
        return False
    else:
        return True


async def get_fb_lang(page: Page) -> str | None:
    """
    Get the language of the Facebook user interface.
    :param page: The browser page instance.
    """
    try:
        await navigate(page, FACEBOOK_URL + "/groups/feed/")

        lang = await page.locator("html").get_attribute("lang")
    except Error:
        return None
    else:
        if lang in SUPPORTED_FB_LANGUAGES:
            return lang

    return None


async def navigate(page: Page, url: str) -> None:
    """
    Navigates to the given URL.
    Errors are handled by the caller function.
    :param page: The browser page instance.
    :param url: The URL to navigate to.
    """
    await page.goto(url)
