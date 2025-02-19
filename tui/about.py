from textual.app import ComposeResult
from textual.containers import Center, Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Link

from _version import __version__
from constants import EMAIL


class About(ModalScreen):
    def compose(self) -> ComposeResult:
        with Grid():
            yield Label("Automate Facebook Posts", classes="label")
            yield Label(f"Version: {__version__}", classes="label")
            with Center():
                yield Label("Developed by: ")
                yield Link("@otf31", url=f"mailto:{EMAIL}", tooltip=f"{EMAIL}")
            yield Button("Close", variant="error", action="app.pop_screen")
