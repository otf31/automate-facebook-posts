import fs
from playwright.async_api import Error, async_playwright
from textual import work
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from common_functions import get_configuration_value
from constants import FACEBOOK_URL

MANUAL_MODE_INTRO = (
    "In manual mode, you can interact with the browser and perform tasks manually like "
    "sign in into your Facebook account, choosing a profile and so on.\n\n"
    "Pressing the [b]Close[/b] button will close the browser window."
)


class ManualMode(ModalScreen[None]):
    DEFAULT_CSS = """
    ManualMode {
        align: center middle;

        Grid {
            grid-size: 1;
            grid-rows: 1fr auto;
            grid-gutter: 1 2;
            width: 60;
            height: 11;
            padding: 0 1;
            border: thick $background 80%;
            background: $surface;

            Label {
                height: 1fr;
                content-align: center middle;
            }

            Button {
                width: 100%;
            }
        }
    }
    """

    def compose(self) -> ComposeResult:
        with Grid():
            yield Label(MANUAL_MODE_INTRO)
            yield Button("Close", "error", action="app.pop_screen")

    def on_mount(self):
        self.launch_browser()

    @work
    async def launch_browser(self):
        chrome_binary_path = get_configuration_value("CHROME_BINARY_PATH")
        posts_folder_path = get_configuration_value("POSTS_FOLDER_PATH")
        chrome_data_dir = fs.path.combine(posts_folder_path, "/profile")
        headless = False

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch_persistent_context(
                    executable_path=chrome_binary_path,
                    headless=headless,
                    user_data_dir=chrome_data_dir,
                )
                page = browser.pages[0]

                await page.goto(FACEBOOK_URL)

                # Keep the browser open until the user closes it manually or the screen
                # is popped. A timeout of 0 means that the function will wait
                # indefinitely. When resolved, the browser will be closed and the
                # screen will be popped.
                await page.wait_for_event(
                    "close", predicate=lambda x: self.app.pop_screen(), timeout=0
                )
        except Error as e:
            self.app.pop_screen()  # noqa
            self.notify(e.message, severity="warning")
