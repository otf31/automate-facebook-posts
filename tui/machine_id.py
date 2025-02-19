import copykitten
from copykitten import CopykittenError
from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from subscription import get_device_id


class MachineId(ModalScreen):
    def compose(self) -> ComposeResult:
        with Grid():
            yield Label("Your device ID", id="id-label")
            yield Label(get_device_id(), id="id-value")
            yield Button(
                "Close", variant="error", id="close-button", action="app.pop_screen"
            )
            yield Button("Copy", variant="primary", id="copy-button")

    @on(Button.Pressed, "#copy-button")
    def copy(self):
        try:
            copykitten.copy(get_device_id())
        except CopykittenError:
            self.app.notify("Failed to copy ID", severity="error")
        else:
            self.app.notify("ID copied to clipboard")
