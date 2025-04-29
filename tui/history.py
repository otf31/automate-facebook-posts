import csv

from fs import open_fs
from fs.errors import FileExpected, ResourceNotFound
from textual.app import ComposeResult
from textual.containers import Center, Container
from textual.screen import Screen
from textual.widgets import Button, DataTable, Label

from common_functions import get_configuration_value
from constants import HiSTORY_FILE_PATH


class History(Screen):
    DEFAULT_CSS = """
    History {
        padding: 1 2;

        Container {
            align-horizontal: center;
        }

        DataTable {
            height: 1fr;
            width: auto;
        }

        Center {
            margin-top: 1;
        }
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("History", classes="header")
        with Container():
            yield DataTable()
        with Center():
            yield Button("Close", variant="error", action="app.pop_screen")

    def load(self):
        posts_folder_path = get_configuration_value("POSTS_FOLDER_PATH")
        data_table = self.query_one(DataTable)

        # Clear data table, rows and columns
        data_table.clear(columns=True)

        with open_fs(posts_folder_path) as posts_folder_fs:
            try:
                with posts_folder_fs.open(HiSTORY_FILE_PATH) as history_file:
                    reader = csv.reader(history_file, delimiter=";")

                    data_table.add_columns(*next(reader))

                    for row in reader:
                        data_table.add_row(*row)
            except (ResourceNotFound, FileExpected):
                self.app.notify("No history file found", severity="warning")
                self.app.pop_screen()

    def on_screen_resume(self):
        self.load()
