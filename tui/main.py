from typing import Literal

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Button, Footer, Label

from _version import __version__
from about import About
from common_functions import validate_conf_file
from configuration import Configuration
from log import Logs
from machine_id import MachineId
from manual_mode import ManualMode
from publish import Publish
from subscription import get_subscription_status

INTRO = """
Streamline your group engagement with our automation tool. 
[bold]Publish to multiple Facebook groups in just a few clicks[/], no more manual posting!
Perfect for admins and members looking to save time and stay active.
Simplify your group management today!
"""


class Autofbpost(App[None]):
    CSS_PATH = "styles.tcss"
    AUTO_FOCUS = None
    ENABLE_COMMAND_PALETTE = False
    SCREENS = {
        "publish": Publish,
        "manual-mode": ManualMode,
        "machine-id": MachineId,
        "configuration": Configuration,
        "logs": Logs,
        "about": About,
    }
    BINDINGS = {
        Binding("ctrl+q", "", "Quit", show=False),
        ("l", "push_screen('logs')", "Logs"),
        ("c", "push_screen('configuration')", "Configuration"),
        ("a", "push_screen('about')", "About"),
    }
    need_subscription_buttons = ["#publish", "#manual-mode"]

    def compose(self) -> ComposeResult:
        yield Label(
            "[b cyan]Auto[/]mate [b cyan]F[/]ace[b cyan]b[/]ook [b cyan]Post[/]s"
            f" v{__version__}",
            classes="header",
        )
        yield Label(INTRO, classes="screen-intro")
        with Grid(id="buttons"):
            yield Button("Publish", id="publish")
            yield Button("Manual mode", id="manual-mode")
            yield Button("Id", id="id")
            yield Button("Exit", variant="error", action="app.quit")
        yield Footer()

    def set_buttons_state(self, action: Literal["enable", "disable"]):
        for button_id in self.need_subscription_buttons:
            self.query_one(button_id).disabled = action == "disable"

    @on(Button.Pressed, "#publish")
    def show_publish_screen(self):
        publish_button = self.query_one("#publish")

        publish_button.loading = True
        self.set_buttons_state("disable")
        self.check_subscription(publish_button, Publish())

    @on(Button.Pressed, "#manual-mode")
    def show_manual_mode_screen(self):
        manual_mode_button = self.query_one("#manual-mode")

        manual_mode_button.loading = True
        self.set_buttons_state("disable")
        self.check_subscription(manual_mode_button, ManualMode())

    @on(Button.Pressed, "#id")
    def show_id_screen(self):
        self.push_screen(MachineId())

    @work
    async def check_subscription(self, button: Button, screen: Screen) -> None:
        has_subscribtion, msg = await get_subscription_status()

        # Reset loading state
        button.loading = False

        # Restore buttons state
        self.set_buttons_state("enable")

        if has_subscribtion:
            await self.push_screen(screen)
        else:
            self.notify(msg, severity="error")

    def on_load(self):  # noqa
        # Write default configuration if there is no configuration file
        validate_conf_file()


if __name__ == "__main__":
    app = Autofbpost()

    app.run()
