from textual.app import ComposeResult
from textual.containers import Center, Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Link

from _version import __version__
from constants import EMAIL, WEBPAGE_URL


class About(ModalScreen):
    def compose(self) -> ComposeResult:
        with Grid():
            with Center():
                yield Label(
                    "[b cyan]Auto[/]mate [b cyan]F[/]ace[b cyan]b[/]ook [b cyan]Post[/]s"
                )
            with Center():
                yield Label(f"Version: {__version__}", variant="primary")
            with Center():
                yield Label("Developed by: ")
                yield Link("@otf31", url=f"mailto:{EMAIL}", tooltip=EMAIL)
            with Center():
                yield Label("Visit us ")
                yield Link("here", url=WEBPAGE_URL, tooltip=WEBPAGE_URL)
            yield Button("Close", variant="error", action="app.pop_screen")
