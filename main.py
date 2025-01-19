import csv
import random
import re
from datetime import datetime
from time import sleep
from typing import Annotated, Optional

import click
import fs
import typer
from fs import open_fs
from playwright.sync_api import sync_playwright, expect, Error
from rich.pretty import Pretty
from rich.progress import track
from rich.prompt import Confirm
from rich.status import Status

import login
from common_functions import print_panel, validate_path, launch_browser, \
    navigate, wait_random_seconds, exit_app, is_logged_in
from constants import CHROME_BINARY_PATH, POSTS_FOLDER_PATH

available_posts = []


def pick_random_description(descriptions: list[str]) -> str:
    """
    Pick a random description from a list of descriptions.
    :param descriptions: A list containing the descriptions.
    :return: A single random description.
    """
    description: str = random.choice(descriptions)

    return description


def read_filters(filters_file_path: str) -> list[str]:
    """
    Read the publication filters from a file.
    The filters must be separated by commas.
    :param filters_file_path: The filters file path.
    :return: A list of filters.
    """
    parent = fs.path.dirname(filters_file_path)

    with open_fs(parent) as parent_fs:
        with parent_fs.open(fs.path.basename(filters_file_path)) as filters_file:
            text = filters_file.read()

            return [f.strip().lower() for f in text.split(",")]


def read_groups(groups_file_path: str, publication_filters: list[str]) -> list[list[str]]:
    """
    Read groups from a CSV file.
    :param groups_file_path: The groups file path.
    :param publication_filters: The filters to match the groups.
    :return: A list of filtered groups according to publication_filters.
    """

    groups = []
    head, tail = fs.path.split(groups_file_path)

    with open_fs(head) as parent_fs:
        with parent_fs.open(tail) as groups_file:
            reader = csv.reader(groups_file, delimiter=";")

            # Skip the header
            next(reader)

            rows = list(reader)

            for row in rows:
                group_filters = [gf.strip().lower() for gf in row[2].split(",")]

                if len(set(publication_filters).intersection(set(group_filters))) > 0:
                    groups.append(row)

    return groups


def get_descriptions(descriptions_folder_path: str) -> list[str]:
    """
    Get descriptions from .txt files from a folder.
    :param descriptions_folder_path: The descriptions folder path.
    :return: A list containing the descriptions as strings and stripped.
    """
    descriptions = []

    with open_fs(descriptions_folder_path) as descriptions_fs:
        d = descriptions_fs.filterdir(
            "/",
            files=["*.txt"],
            exclude_dirs=["*"]
        )

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
    images = []

    with open_fs(images_folder_path) as images_fs:
        i = images_fs.filterdir(
            "/",
            files=["*.jpg", "*.jpeg", "*.png"],
            exclude_dirs=["*"],
            namespaces=["details"]
        )

        for file in i:
            images.append(images_fs.getsyspath(file.name))

    return images


cli = typer.Typer(no_args_is_help=True)
cli.add_typer(login.cli)


@cli.command()
def publish(
        ctx: typer.Context,
        post: Annotated[
            str,
            typer.Option(
                help="The post",
                prompt="Select a post",
                show_choices=True,
                click_type=click.Choice(available_posts)
            )
        ]
):
    """
    Publish posts.
    """
    posts_folder_path = fs.path.abspath(ctx.obj["posts_folder_path"])
    post_path = fs.path.combine(posts_folder_path, post)
    images_folder_path = fs.path.combine(post_path, "images")
    descriptions_folder_path = fs.path.combine(post_path, "descriptions")
    filters_file_path = fs.path.combine(post_path, "filters.txt")
    groups_file_path = fs.path.combine(posts_folder_path, "groups.csv")

    # Validate images folder
    validate_path(images_folder_path, "dir")

    # Validate descriptions folder
    validate_path(descriptions_folder_path, "dir", min_files=3)

    # Validate groups file
    validate_path(groups_file_path, "file")

    # Validate filters file
    validate_path(filters_file_path, "file")

    # Images
    images = get_images(images_folder_path)

    print_panel(f"Found {len(images)} images")

    descriptions = get_descriptions(descriptions_folder_path)

    # Print a random description
    print_panel(pick_random_description(descriptions), title="Random description")

    # Filters
    publication_filters = read_filters(filters_file_path)

    print_panel(Pretty(publication_filters), title="Filters")

    # Groups
    groups = read_groups(groups_file_path, publication_filters)
    num_groups = len(groups)
    groups_with_errors = []

    print_panel(
        f"This post is going to be publish in [blue]{num_groups}[/] groups, do "
        f"not close the terminal or the browser until the process is "
        f"completed"
    )

    with sync_playwright() as p:
        with Status("Initializing ...") as status:
            status.update("Launching browser ...")

            page = launch_browser(ctx, p)

            status.update("Checking if the user is logged in...")

            if not is_logged_in(page):
                print_panel(
                    "You are not logged in, [blue]please sign in manually into your "
                    "Facebook account[/blue] using the [blue]login[/blue] command and "
                    "set your Facebook profile if necessary, then try again",
                    msg_type="error"
                )

        is_user_ready = Confirm.ask("Do you want to start the publication process?")

        if not is_user_ready:
            exit_app()

        for index, group in enumerate(track(groups, "Publishing...")):
            try:
                group_name = group[0]
                group_url = group[1]
                group_info = f"{group_name} - {group_url}"

                print_panel(group_info)

                try:
                    # Navigate to the group
                    navigate(page, group_url)

                    sleep(2)

                    if "| Facebook" not in page.title():
                        print_panel(
                            f"Group {group_name} does not exist or is not "
                            f"available",
                            msg_type="warning"
                        )

                        continue

                    write_something = page.get_by_role(
                        "button",
                        name=re.compile("Write something.*")
                    )
                    start_discussion = page.get_by_role(
                        "button",
                        name=re.compile("Start discussion.*")
                    )

                    try:
                        expect(
                            write_something.or_(start_discussion)
                        ).to_be_visible(timeout=3000)

                        if write_something.is_visible():
                            write_something.click(force=True)
                        elif start_discussion.is_visible():
                            start_discussion.click(force=True)
                    except AssertionError:
                        page.locator(
                            "a[href*='buy_sell_discussion']"
                        ).click(force=True)

                        page.wait_for_url(
                            re.compile(".*/buy_sell_discussion")
                        )

                        sleep(2)

                        try:
                            expect(
                                write_something.or_(start_discussion)
                            ).to_be_visible(timeout=3000)

                            if write_something.is_visible():
                                write_something.click(force=True)
                            elif start_discussion.is_visible():
                                start_discussion.click(force=True)
                        except AssertionError:
                            groups_with_errors.append(
                                (group_name, group_url,
                                 "Cannot find any way to post")
                            )

                            continue

                    post_button = page.get_by_role(
                        "button", name="Post", exact=True
                    )
                    post_button.wait_for()

                    textarea_create_public_post = page.get_by_label(
                        re.compile("Create a public post.*")
                    )
                    textarea_write_something = page.get_by_label(
                        re.compile("Write something.*")
                    )

                    # Expect the textarea to be visible
                    expect(
                        textarea_create_public_post.or_(textarea_write_something)
                    ).to_be_visible()

                    description = pick_random_description(descriptions)

                    # Fill the description
                    if textarea_write_something.is_visible():
                        textarea_write_something.fill(description)
                    elif textarea_create_public_post.is_visible():
                        textarea_create_public_post.fill(description)

                    # Find Photo/Video element and click it
                    photo_video = page.get_by_label("Photo/video")

                    photo_video.click(force=True)

                    # Get the file input element
                    file_input = page.locator(
                        '[accept="image/*,image/heif,image/heic,video/*,'
                        'video/mp4,video/x-m4v,video/x-matroska,.mkv"]')

                    # Upload the images
                    file_input.set_input_files(images)

                    sleep(2)

                    # Press the Post button
                    post_button.click(force=True)

                    # Posting element
                    posting_el = page.get_by_text(re.compile("Posting.*"))

                    # Wait until the posting text is detached
                    posting_el.wait_for(state="detached")

                    print_panel(
                        f"The post has been submitted to {group_name}", msg_type="success"
                    )
                # Playwright Error
                except Error as e:
                    groups_with_errors.append((group_name, group_url, e.message))

                    continue
                # Any exception
                except Exception as e:
                    groups_with_errors.append((group_name, group_url, str(e)))

                    continue

                # Do not wait if the last group is reached
                if index < num_groups - 1:
                    # Wait a random time between 90 seconds and 130 seconds
                    if (index + 1) % 5 == 0:
                        wait_random_seconds(90, 130)
                    # Wait a random time between 45 seconds and 65 seconds
                    else:
                        wait_random_seconds(45, 65)
            except IndexError as e:
                print_panel(f"{e}", msg_type="warning")
                continue

        print_panel("The task has been completed", msg_type="success")

        if groups_with_errors:
            print_panel("Groups with errors", msg_type="warning")
            for group in groups_with_errors:
                print_panel(f"{group[0]} - {group[1]} - {group[2]}", msg_type="warning")

        # Write to a file log
        # publication timestamp groups without_errors num_failed
        num_failed = len(groups_with_errors)
        num_submitted = num_groups - num_failed
        line = [post, datetime.now(), num_groups, num_submitted, num_failed]

        with open_fs(posts_folder_path) as posts_folder_fs:
            logs_file_name = "log.csv"

            with posts_folder_fs.open(logs_file_name, "a") as log_file:
                writer = csv.writer(log_file, delimiter=";")

                if log_file.tell() == 0:
                    writer.writerow(
                        ["Post", "Timestamp", "Total groups", "Submitted", "Failed"]
                    )

                writer.writerow(line)


@cli.callback()
def callback(
        ctx: typer.Context,
        chrome_binary_path: Annotated[
            Optional[str],
            typer.Option(
                help="The Chrome binary path"
            )
        ] = CHROME_BINARY_PATH,
        headless: Annotated[
            Optional[bool],
            typer.Option(
                help="Run the browser in headless mode"
            )
        ] = True,
        posts_folder_path: Annotated[
            Optional[str],
            typer.Option(
                help="The folder containing the posts"
            )
        ] = POSTS_FOLDER_PATH
):
    """
    Automate facebook posts.
    """
    with open_fs(posts_folder_path) as posts_folder_fs:
        # Find available posts
        if not posts_folder_fs.exists("/"):
            print_panel(f"Folder {posts_folder_path} does not exist", msg_type="error")
        else:
            # Profile folder (create if not exists)
            posts_folder_fs.makedir("/profile", recreate=True)

            for path in posts_folder_fs.filterdir(
                    "/", exclude_files=["*"], exclude_dirs=["profile"]
            ):
                available_posts.append(path.name)

            if not available_posts:
                print_panel(f"No posts found in {posts_folder_path}", msg_type="error")

            ctx.obj = {
                "chrome_binary_path": chrome_binary_path,
                "headless": headless,
                "posts_folder_path": posts_folder_path
            }


if __name__ == "__main__":
    cli()
