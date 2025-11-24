import csv
import re
import secrets
from asyncio import sleep
from datetime import datetime
from typing import Literal

import fs
from fs import open_fs
from fs.errors import CreateFailed
from fs.opener.errors import OpenerError
from playwright.async_api import Error, Page, async_playwright, expect
from rich.pretty import Pretty
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Center, Horizontal, VerticalGroup
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Label, ProgressBar, RichLog, Select

from browser_utils import get_fb_lang, is_logged_in, navigate
from common_functions import (
    StyledPanel,
    get_configuration_value,
    get_locales_fb_strings,
    panels_group,
    wait_random_seconds,
)
from constants import SUPPORTED_FB_LANGUAGES, HiSTORY_FILE_PATH


def pick_random_description(descriptions: list[str]) -> str:
    """
    Pick a random description from a list of descriptions.
    :param descriptions: A list containing the descriptions.
    :return: A single random description.
    """
    description: str = secrets.choice(descriptions)

    return description


def read_filters(filters_file_path: str) -> list[str]:
    """
    Read the publication filters from a file.
    The filters must be separated by commas.
    :param filters_file_path: The filters file path.
    :return: A list of filters.
    """
    folder, file = fs.path.split(filters_file_path)

    with open_fs(folder) as dir_fs:
        with dir_fs.open(file) as filters_file:
            text = filters_file.read()

    return [f.strip().lower() for f in text.split(",")]


def read_groups(
    groups_file_path: str, publication_filters: list[str]
) -> list[list[str]]:
    """
    Read groups from a CSV file and randomize them.
    :param groups_file_path: The groups file path.
    :param publication_filters: The filters to match the groups.
    :return: A list of filtered groups according to publication_filters.
    """
    system_random = secrets.SystemRandom()
    groups = []
    folder, resource = fs.path.split(groups_file_path)

    with open_fs(folder) as dir_fs:
        with dir_fs.open(resource) as groups_file:
            reader = csv.reader(groups_file, delimiter=";")

            # Skip the header
            next(reader)

            rows = list(reader)

    for row in rows:
        group_filters = [gf.strip().lower() for gf in row[2].split(",")]

        if len(set(publication_filters).intersection(set(group_filters))) > 0:
            groups.append(row)

    # Randomize the groups
    system_random.shuffle(groups)

    return groups


def get_descriptions(descriptions_folder_path: str) -> list[str]:
    """
    Get descriptions from .txt files from a folder.
    :param descriptions_folder_path: The descriptions folder path.
    :return: A list containing the descriptions as strings and stripped.
    """
    descriptions: list[str] = []

    with open_fs(descriptions_folder_path) as descriptions_fs:
        d = descriptions_fs.filterdir("/", files=["*.txt"], exclude_dirs=["*"])

        for file in d:
            with descriptions_fs.open(file.name) as description_file:
                descriptions.append(description_file.read().strip())

    return descriptions


def get_images(images_folder_path: str) -> list[str]:
    """
    Get images from a folder. The images must be in jpg, jpeg or png format.
    :param images_folder_path: The images folder path.
    :return: A list of containing the images absolute paths.
    """

    def natural_sort_key(s):
        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split(r"(\d+)", s)
        ]

    images = []

    with open_fs(images_folder_path) as images_fs:
        i = images_fs.filterdir(
            "/", files=["*.jpg", "*.jpeg", "*.png"], exclude_dirs=["*"]
        )

        for file in i:
            images.append(images_fs.getsyspath(file.name))

    return sorted(images, key=natural_sort_key)


class Publish(Screen):
    DEFAULT_CSS = """
    Publish {
        padding: 1 2;

        Horizontal {
            height: auto;
            margin-bottom: 1;
            
            #stop {
                display: none
            }
        }
        
        #close {
            margin-top: 1;
        }
        
        &.started #start {
            display: none
        }
        
        &.started #stop {
            display: block
        }
        
        &.started #close {
            display: none
        }
        
        RichLog {
            height: 1fr;
        }
        
        ProgressBar {
            display: none;
            margin-top: 1;
        }
        
        &.started ProgressBar {
            display: block;
        }
        
        #extra-info {
            display: none;
        }
    }
    """

    available_posts: reactive[list[tuple[str, str]]] = reactive(list, recompose=True)
    started: reactive[bool] = reactive(False, toggle_class="started")

    def __init__(self):
        super().__init__()
        self.posts_folder_path: str = get_configuration_value("POSTS_FOLDER_PATH")
        self.post_path: str | None = None
        self.images_folder_path: str | None = None
        self.descriptions_folder_path: str | None = None
        self.filters_file_path: str | None = None
        self.groups_file_path: str | None = None
        self.publication_filters: list[str] | None = None
        self.groups: list[list[str]] | None = None
        self.num_groups: int | None = None

    def compose(self) -> ComposeResult:
        yield Label("Publish", classes="header")
        with Horizontal():
            with VerticalGroup():
                yield Select(options=self.available_posts)
                yield Label(id="extra-info", variant="accent")
            yield Button("Start", id="start")
            yield Button(
                "Stop & Quit", id="stop", variant="error", action="app.pop_screen"
            )
        yield RichLog()
        with Center():
            yield ProgressBar(show_eta=False)
        with Center():
            yield Button("Close", id="close", variant="error", action="app.pop_screen")

    def on_screen_resume(self):
        self.load_options()

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed):
        """
        This method will validate files and directories, if there is an error, then the
        select will have its default value (BLANK)
        """
        extra_info = self.query_one("#extra-info", Label)

        if (post := event.value) == Select.BLANK:
            extra_info.display = "none"

            return

        self.post_path = fs.path.combine(self.posts_folder_path, post)
        self.images_folder_path = fs.path.combine(self.post_path, "images")
        self.descriptions_folder_path = fs.path.combine(self.post_path, "descriptions")
        self.filters_file_path = fs.path.combine(self.post_path, "filters.txt")
        self.groups_file_path = fs.path.combine(self.posts_folder_path, "groups.csv")

        # Validate images folder
        first_validation = self.validate_path(
            self.images_folder_path, "dir", dir_file_type=["*.jpg", "*.jpeg", "*.png"]
        )

        # Validate descriptions folder
        second_validation = self.validate_path(
            self.descriptions_folder_path, "dir", min_files=3, dir_file_type=["*.txt"]
        )

        # Validate groups file
        third_validation = self.validate_path(self.groups_file_path, "file")

        # Validate filters file
        fourth_validation = self.validate_path(self.filters_file_path, "file")

        if not (
            first_validation
            and second_validation
            and third_validation
            and fourth_validation
        ):
            self.query_one(Select).value = Select.BLANK

            return

        # Filters
        self.publication_filters = read_filters(self.filters_file_path)

        # Groups
        self.groups = read_groups(self.groups_file_path, self.publication_filters)

        self.num_groups = len(self.groups)

        # Show extra information
        extra_info.update(
            f"{', '.join(self.publication_filters)} | {self.num_groups} groups"
        )
        extra_info.display = "block"

    @on(Button.Pressed, "#start")
    def start_publish(self) -> None:
        select = self.query_one(Select)

        if (post := select.value) == Select.BLANK:
            self.app.notify("Select a post", severity="warning")
            return

        # Apply .started class
        self.started = True

        # Disable the select
        select.disabled = True

        # Start the publication process
        self.start_process(post)

    @work
    async def start_process(self, post: str) -> None:
        chrome_binary_path = get_configuration_value("CHROME_BINARY_PATH")
        posts_folder_path = get_configuration_value("POSTS_FOLDER_PATH")
        chrome_data_dir = fs.path.combine(posts_folder_path, "/profile")
        headless = get_configuration_value("HEADLESS")
        log = self.query_one(RichLog)
        progress_bar = self.query_one(ProgressBar)

        # Images
        images = get_images(self.images_folder_path)

        log.write(StyledPanel(f"Found {len(images)} images"))

        descriptions = get_descriptions(self.descriptions_folder_path)

        # Print a random description
        log.write(
            StyledPanel(
                pick_random_description(descriptions), title="Random description"
            )
        )

        # Log filters
        log.write(StyledPanel(Pretty(self.publication_filters), title="Filters"))

        # Groups
        groups_with_warnings: list[tuple[str, str, str]] = []
        groups_with_errors: list[tuple[str, str, str]] = []

        # Set progress bar total
        progress_bar.total = self.num_groups

        log.write(
            StyledPanel(
                f"This post is going to be publish in [blue]{self.num_groups}[/] groups, "
                "do not exit the terminal or close the browser until the "
                "process is completed"
            )
        )

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch_persistent_context(
                    executable_path=chrome_binary_path,
                    headless=headless,
                    user_data_dir=chrome_data_dir,
                )
                page: Page = browser.pages[0]

                # Get user facebook interface language
                if not (lang := await get_fb_lang(page)):
                    self.app.pop_screen()  # noqa

                    self.notify(
                        f"Unsupported Facebook language. "
                        "Please switch to one of these languages: "
                        f"{', '.join(SUPPORTED_FB_LANGUAGES.values())}."
                        " Then try again.",
                        severity="error",
                        timeout=10,
                    )

                fb_locale_strs = get_locales_fb_strings(lang)
                publish_strs = fb_locale_strs["publish"]

                log.write(
                    StyledPanel(
                        fb_locale_strs["language"], title="Facebook user language"
                    )
                )

                if not await is_logged_in(
                    page, fb_locale_strs["login"]["groups_page_title"]
                ):
                    self.app.pop_screen()  # noqa

                    self.notify(
                        "You are not logged in Facebook, please login using "
                        "manual option in main menu, then try again.",
                        severity="error",
                    )
                    return

                for index, group in enumerate(self.groups):
                    try:
                        group_name = group[0]
                        group_url = group[1]
                    except IndexError as e:
                        log.write(StyledPanel(f"{e}", msg_type="warning"))

                        # Advance progress bar
                        progress_bar.advance(1)

                        continue
                    else:
                        group_info = f"{group_name} - {group_url}"

                    log.write(StyledPanel(group_info))

                    await sleep(3)

                    try:
                        # Navigate to the group
                        await navigate(page, group_url)

                        await sleep(2)

                        if "| Facebook" not in await page.title():
                            groups_with_errors.append(
                                (
                                    group_name,
                                    group_url,
                                    "Group does not exist or is not available",
                                )
                            )

                            # Advance progress bar
                            progress_bar.advance(1)

                            continue

                        write_something = page.get_by_role(
                            "button",
                            name=re.compile(publish_strs["button_write_something"]),
                        )
                        start_discussion = page.get_by_role(
                            "button",
                            name=re.compile(publish_strs["button_start_discussion"]),
                        )

                        try:
                            await expect(
                                write_something.or_(start_discussion)
                            ).to_be_visible(timeout=3000)
                        except AssertionError:
                            await page.get_by_role(
                                "tab",
                                name=re.compile(publish_strs["tab_discussion"]),
                            ).click(force=True, timeout=5000)

                            await sleep(2)

                            try:
                                await expect(
                                    write_something.or_(start_discussion)
                                ).to_be_visible(timeout=3000)
                            except AssertionError:
                                groups_with_errors.append(
                                    (
                                        group_name,
                                        group_url,
                                        "Cannot find any way to post",
                                    )
                                )

                                # Advance progress bar
                                progress_bar.advance(1)

                                continue

                        # Check if the group has pending posts
                        pending_posts_el = page.get_by_text(
                            re.compile(publish_strs["text_pending_posts"])
                        )

                        if await pending_posts_el.is_visible():
                            pending_posts_text = await pending_posts_el.text_content()
                            pending_posts = pending_posts_text.split()[0]

                            groups_with_warnings.append(
                                (
                                    group_name,
                                    group_url,
                                    f"Group has {pending_posts} pending posts",
                                )
                            )

                        if await write_something.is_visible():
                            await write_something.click(force=True)
                        elif await start_discussion.is_visible():
                            await start_discussion.click(force=True)

                        # Posting loading
                        posting_el = page.get_by_text(
                            re.compile(publish_strs["loader_posting"])
                        )

                        post_button = page.get_by_role(
                            "button", name=publish_strs["button_post"], exact=True
                        )

                        # Wait for the post button to be visible
                        await post_button.wait_for(timeout=6000)

                        # Textarea elements
                        textarea_create_post = page.locator(
                            '[aria-placeholder*="'
                            f'{publish_strs["textarea_create_post"]}"]'
                        )
                        textarea_write_something = page.locator(
                            '[aria-placeholder*="'
                            f'{publish_strs["textarea_write_something"]}"]'
                        )

                        textarea = textarea_create_post.or_(textarea_write_something)

                        # Expect the textarea to be visible
                        await expect(textarea).to_be_visible()

                        description = pick_random_description(descriptions)

                        # Fill the description
                        await textarea.fill(description)

                        # Get the file input element
                        file_input = page.locator(
                            '[accept="image/*,image/heif,image/heic,video/*,'
                            'video/mp4,video/x-m4v,video/x-matroska,.mkv"]',
                        ).last

                        try:
                            await expect(file_input).to_be_attached()
                        except AssertionError:
                            # If the file_input is not present, then click the
                            # Photo/video button
                            photo_video = page.get_by_label(
                                publish_strs["button_photo_video"]
                            )

                            await photo_video.click(force=True)
                            await expect(file_input).to_be_attached()

                        await wait_random_seconds(3, 4)

                        # Upload the images
                        await file_input.set_input_files(images)

                        await wait_random_seconds(1)

                        # Expect the post button to be enabled
                        await expect(post_button).to_be_enabled()

                        await wait_random_seconds(2, 3)

                        # Press the Post button
                        await post_button.click(force=True)

                        # Wait until the posting text is visible
                        await posting_el.wait_for(timeout=6000)

                        # Wait until the posting text is detached
                        await posting_el.wait_for(state="detached")

                        log.write(
                            StyledPanel(
                                f"The post has been submitted to {group_name}",
                                msg_type="success",
                            )
                        )

                        # Do not wait if the last group is reached
                        if index < self.num_groups - 1:
                            # Wait a random time between 115 seconds and 148 seconds
                            if (index + 1) % 5 == 0:
                                await wait_random_seconds(115, 148)
                            # Wait a random time between 60 seconds and 75 seconds
                            else:
                                await wait_random_seconds(60, 75)
                    # Playwright Error
                    except Error as e:
                        groups_with_errors.append((group_name, group_url, e.message))
                        await wait_random_seconds(10, 15)
                    # Any exception
                    except Exception as e:
                        groups_with_errors.append((group_name, group_url, str(e)))
                        await wait_random_seconds(5)

                    # Advance progress bar
                    progress_bar.advance(1)

                # The proccess has been completed
                log.write(
                    StyledPanel("The task has been completed", msg_type="success")
                )

                # Write to history file
                if (num_with_warnings := len(groups_with_warnings)) > 0:
                    log.write(
                        panels_group(
                            groups_with_warnings,
                            extract_msg=lambda x: f"{x[0]} - {x[1]} - {x[2]}",
                            title=f"Groups with warnings ({num_with_warnings})",
                            children_msg_type="warning",
                        )
                    )

                if (num_failed := len(groups_with_errors)) > 0:
                    log.write(
                        panels_group(
                            groups_with_errors,
                            extract_msg=lambda x: f"{x[0]} - {x[1]} - {x[2]}",
                            title=f"Groups with errors ({num_failed})",
                            children_msg_type="error",
                        )
                    )

                # publication timestamp groups without_errors num_failed
                headers = ["Post", "Date", "Total groups", "Submitted", "Failed"]

                line = [
                    post,
                    datetime.now().strftime("%a %d %B %Y, %I:%M%p"),
                    self.num_groups,
                    self.num_groups - num_failed,
                    num_failed,
                ]

                with open_fs(posts_folder_path) as posts_folder_fs:
                    history_file_path = HiSTORY_FILE_PATH

                    if not posts_folder_fs.exists(history_file_path):
                        with posts_folder_fs.open(
                            history_file_path, "w"
                        ) as history_file:
                            writer = csv.writer(history_file, delimiter=";")

                            writer.writerow(headers)

                    with posts_folder_fs.open(history_file_path, "a") as history_file:
                        writer = csv.writer(history_file, delimiter=";")

                        writer.writerow(line)

                # Remove .started class
                self.started = False

                # Hide the start button
                self.query_one("#start", Button).display = False

                # Keep showing the progress bar
                progress_bar.display = True

                if not headless:
                    # Keep the browser open until the user closes it manually or cancel
                    # the process. A timeout of 0 means that the function will wait
                    # indefinitely. When resolved, the browser will be closed and the
                    # screen will be popped.
                    await page.wait_for_event(
                        "close", predicate=lambda x: self.app.pop_screen(), timeout=0
                    )
        except Error as e:
            self.app.pop_screen()  # noqa
            self.notify(e.message, severity="error")

    def notify_post_validation_error(self, msg: str) -> None:
        self.notify(msg, severity="error")

    def validate_path(
        self,
        path: str,
        type_: Literal["file", "dir"],
        min_files: int = None,
        dir_file_type: list[str] = None,
    ) -> bool:
        """
        Validate the existence of a file or directory.
        :param path: Absolute path to the resource.
        :param type_: The type of the resource: file or dir.
        :param min_files: If the resource is a directory,
            the minimum number of files it must contain. Default is None.
        :param dir_file_type: The file types to filter in a directory. Default is None.
        :raise fs.opener.errors.OpenerError: Opening a filesystem with an invalid path.
        """
        folder, resource = fs.path.split(path)
        res_s = f"[b]{resource}[/]"
        type_s = f"[b]{type_}[/]"
        is_valid = True

        try:
            with open_fs(folder) as root_fs:
                if not root_fs.exists(resource):
                    self.notify_post_validation_error(
                        f"Resource {res_s} of type {type_s} does not exist in {folder}"
                    )

                    return False

                if type_ == "file":
                    if not root_fs.isfile(resource):
                        self.notify_post_validation_error(f"{res_s} is not a file")

                        is_valid = False
                    elif root_fs.getsize(resource) == 0:
                        self.notify_post_validation_error(f"File {res_s} is empty")

                        is_valid = False
                elif type_ == "dir":
                    if not root_fs.isdir(resource):
                        self.notify_post_validation_error(f"{res_s} is not a directory")

                        is_valid = False
                    elif not root_fs.listdir(resource):
                        self.notify_post_validation_error(f"Folder {res_s} is empty")

                        is_valid = False
                    elif (
                        min_files is not None
                        and len(
                            list(
                                root_fs.filterdir(
                                    resource, files=dir_file_type, exclude_dirs=["*"]
                                )
                            )
                        )
                        < min_files
                    ):
                        self.notify_post_validation_error(
                            f"Folder {res_s} must contain at least {min_files} files "
                            f"with type {dir_file_type}."
                        )

                        is_valid = False
        except OpenerError:
            self.notify_post_validation_error(f"Path {folder} does not exist")

            is_valid = False

        return is_valid

    def load_options(self):
        try:
            if (
                posts_folder_path := get_configuration_value("POSTS_FOLDER_PATH")
            ) == "":
                raise CreateFailed

            with open_fs(posts_folder_path) as posts_folder_fs:
                # Find available posts
                for folder in posts_folder_fs.filterdir(
                    "/", exclude_files=["*"], exclude_dirs=["profile"]
                ):
                    folder_name = folder.name
                    self.available_posts.append((folder_name, folder_name))
        except CreateFailed:
            self.app.notify(
                "Invalid posts folder path, check configuration.",
                severity="error",
            )
            self.app.pop_screen()
        else:
            self.mutate_reactive(Publish.available_posts)
