import os

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.validation import ValidationResult, Validator
from textual.widgets import Button, Input, Label, Switch

from common_functions import load_configuration, write_conf_file


class ValidDir(Validator):
    def __init__(self, label: str):
        super().__init__()
        self.label = label

    def validate(self, value: str) -> ValidationResult:
        if value == "":
            return self.failure(f"{self.label} cannot be empty")

        if self.is_valid_dir(value):
            return self.success()
        else:
            return self.failure(f"{self.label} is not a valid directory")

    @staticmethod
    def is_valid_dir(value: str) -> bool:
        return os.path.isdir(value)


class Configuration(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Configuration", classes="header")
        with VerticalScroll():
            with Horizontal():
                yield Label("Chrome binary path", classes="label")
                with Container(classes="input-container"):
                    yield Input(None, id="cbp", classes="input")
            with Horizontal():
                yield Label("Posts folder path", classes="label")
                with Container(classes="input-container"):
                    yield Input(
                        "",
                        id="pfp",
                        classes="input",
                        select_on_focus=True,
                        validators=[ValidDir("Posts folder")],
                    )
            with Horizontal():
                yield Label("Headless mode", classes="label")
                with Container(classes="input-container"):
                    yield Switch(False, id="headless", classes="switch")

        with Center():
            yield Button("Cancel", variant="error", action="app.pop_screen")
            yield Button("Save", id="save-button", variant="success")

    def set_config_values(self):
        config = load_configuration()

        chrome_binary = self.query_one("#cbp", Input)
        posts_folder = self.query_one("#pfp", Input)
        headless = self.query_one("#headless", Switch)

        chrome_binary.value = config["CHROME_BINARY_PATH"]
        posts_folder.value = config["POSTS_FOLDER_PATH"]
        headless.value = config["HEADLESS"]

        posts_folder.validate(str(posts_folder.value))

    def on_screen_resume(self) -> None:
        self.set_config_values()

    @on(Button.Pressed)
    def save(self):
        posts_folder = self.query_one("#pfp", Input)

        if not ValidDir.is_valid_dir(posts_folder.value):
            self.notify("Invalid posts folder path", severity="error")

            return

        chrome_binary_path = self.query_one("#cbp", Input).value
        posts_folder_path = self.query_one("#pfp", Input).value
        headless = self.query_one("#headless", Switch).value

        config = {
            "CHROME_BINARY_PATH": chrome_binary_path,
            "POSTS_FOLDER_PATH": posts_folder_path,
            "HEADLESS": headless,
        }

        write_conf_file(config)

        self.app.notify("Configuration saved", timeout=1)
