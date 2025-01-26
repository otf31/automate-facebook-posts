import random
from time import sleep
from typing import Literal, Any, Callable

import fs
import typer
from fs import open_fs
from fs.opener.errors import OpenerError
from rich import print
from rich.console import group
from rich.panel import Panel
from typing_extensions import TypeVar


class StyledPanel(Panel):
    """
    A styled panel with a message and an optional title.
    :param msg: Message inside the panel.
    :param title: Optional panel title.
    :param msg_type: info, error, warning or success.
        If error, the application will exit.
    """

    def __init__(
            self,
            msg: Any,
            title=None,
            msg_type: Literal["info", "error", "warning", "success"] = "info"
    ):
        super().__init__(msg, title=title, expand=False)

        self.msg_type = msg_type
        self.title = title
        self.msg_type = msg_type

        if msg_type == "error":
            self.style = "red"
        elif msg_type == "warning":
            self.style = "yellow"
        elif msg_type == "success":
            self.style = "green"


def print_panel(
        msg: Any,
        title=None,
        msg_type: Literal["info", "error", "warning", "success"] = "info"
) -> None:
    """
    Print a styled panel.
    :param msg: The message inside the panel.
    :param title: The optional panel title.
    :param msg_type: The type of the message: info, error, warning or success.
    """
    styled_panel = StyledPanel(msg, title=title, msg_type=msg_type)

    print(styled_panel)

    if styled_panel.msg_type == "error":
        raise typer.Exit()


T = TypeVar("T")


# def print_panels_group[T]( -> doesn't work in executable file
def print_panels_group(
        iterable: list[T],
        extract_msg_callback: Callable[[T], str],
        title: str = None,
        children_msg_type: Literal["info", "warning", "success"] = "info"
) -> None:
    """
    Print a group of panels.
    :param iterable: The list of items to iterate.
    :param extract_msg_callback: A callable that extracts the message from the item.
    :param title: The title of the main panel.
    :param children_msg_type: The type of the children panels. Default is info.
    """
    @group()
    def get_panels():
        for i in iterable:
            msg = extract_msg_callback(i)

            yield StyledPanel(str(msg), msg_type=children_msg_type)

    print(Panel(get_panels(), title=title))


def validate_path(
        tail: str,
        type_: Literal["file", "dir"],
        min_files: int = None
) -> None:
    """
    Validate the existence of a file or directory.
    :param tail: Absolute path to the resource.
    :param type_: The type of the resource: file or dir.
    :param min_files: If the resource is a directory,
        the minimum number of files it must contain. Default is None.
    :raise fs.opener.errors.OpenerError: Opening a filesystem with an invalid path.
    """
    head, tail = fs.path.split(tail)
    tail_sty = f"[bold blue]{tail}[/]"
    type_sty = f"[blue]{type_}[/]"

    try:
        with open_fs(head) as root_fs:
            if not root_fs.exists(tail):
                print_panel(
                    f"Resource {tail_sty} of type {type_sty} does not exist in {head}",
                    msg_type="error"
                )

            if type_ == "file":
                if not root_fs.isfile(tail):
                    print_panel(f"{tail_sty} is not a file", msg_type="error")
                elif root_fs.getsize(tail) == 0:
                    print_panel(f"File {tail_sty} is empty", msg_type="error")
            elif type_ == "dir":
                if not root_fs.isdir(tail):
                    print_panel(f"{tail_sty} is not a directory", msg_type="error")
                elif not root_fs.listdir(tail):
                    print_panel(f"Folder {tail_sty} is empty", msg_type="error")
                elif min_files is not None and len(root_fs.listdir(tail)) < min_files:
                    print_panel(
                        f"Folder {tail_sty} must contain at least {min_files} files",
                        msg_type="error"
                    )
    except OpenerError:
        print_panel(f"Path {head} does not exist", msg_type="error")


def wait_random_seconds(start: int, end: int = None) -> None:
    """
    Wait a random time between start and end seconds.
    :param start: The start time in seconds
    :param end: The end time in seconds, if None, the end time will be equal to start time
    and the function will wait exactly the start time.
    """
    if end is None:
        end = start

    sleep(random.randint(start, end))
