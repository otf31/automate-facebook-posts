import csv
import random
import re
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Annotated, Optional, List

import click
import typer
from playwright.sync_api import sync_playwright, expect, Error
from rich.progress import track
from rich.prompt import Confirm
from rich.status import Status

import login
from common_functions import print_panel, validate_path, launch_browser, \
    navigate, wait_random_seconds, exit_app, is_logged_in
from constants import CHROME_BINARY_PATH, POST_FOLDER_PATH

available_posts = []


def pick_random_description(descriptions: List[Path]):
    description = random.choice(descriptions)

    with open(description, "r") as description_file:
        return description_file.read().strip()


app = typer.Typer(no_args_is_help=True)
app.add_typer(login.app)


@app.command()
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
    posts_folder_path = Path(ctx.obj["posts_folder_path"])
    post_path = posts_folder_path / post
    images_folder_path = post_path / "images"
    descriptions_folder_path = post_path / "descriptions"
    filters_file_path = post_path / "filters.txt"
    groups_file_path = posts_folder_path / "groups.csv"

    # Validate images folder
    validate_path(images_folder_path, "dir")

    # Validate descriptions folder
    validate_path(descriptions_folder_path, "dir", min_files=3)

    # Validate groups file
    validate_path(groups_file_path, "file")

    # Validate filters file
    validate_path(filters_file_path, "file")

    images_exts = [".jpg", ".jpeg", ".png"]

    # Images
    images = [
        image for image in images_folder_path.iterdir() if
        image.suffix in images_exts
    ]

    print_panel(f"Found {len(images)} images")

    # Descriptions
    descriptions = [
        description for description in descriptions_folder_path.iterdir() if
        description.suffix == ".txt"
    ]

    # Print a random description
    print_panel(pick_random_description(descriptions))

    # Filters
    publication_filters: list[str]
    with open(filters_file_path, "r") as filters_file:
        text = filters_file.read()
        publication_filters = [f.strip().lower() for f in text.split(",")]

    print_panel(f"Filters: {publication_filters}")

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
                    "error"
                )

        is_user_ready = Confirm.ask("Do you want to start the publication process?")

        if not is_user_ready:
            exit_app()

        groups_with_errors = []

        # Read the groups file
        with open(groups_file_path, "r") as groups_file:
            reader = csv.reader(groups_file, delimiter=";")
            rows = list(reader)
            groups = []

            for row in rows:
                group_filters = [gf.strip().lower() for gf in row[2].split(",")]

                if len(set(publication_filters).intersection(set(group_filters))) > 0:
                    groups.append(row)

            num_groups = len(groups)

            print_panel(f"This post is going to be publish in {num_groups} groups, do "
                        f"not close the browser")

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
                                "warning"
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
                        files = [i.absolute().as_posix() for i in images]
                        file_input.set_input_files(files)

                        sleep(2)

                        # Press the Post button
                        post_button.click(force=True)

                        # Posting element
                        posting_el = page.get_by_text(re.compile("Posting.*"))

                        # Wait until the posting text is detached
                        posting_el.wait_for(state="detached")

                        print_panel(
                            f"The post has been submitted to {group_name}", "success"
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
                    if index == num_groups - 1:
                        continue

                    # Wait a random time between 90 seconds and 150 seconds
                    if (index + 1) % 5 == 0:
                        wait_random_seconds(90, 150)
                    # Wait a random time between 35 seconds and 55 seconds
                    else:
                        wait_random_seconds(35, 55)
                except IndexError as e:
                    print_panel(f"{e}", "warning")
                    continue

        print_panel("The task has been completed", "success")

        if groups_with_errors:
            print_panel("Groups with errors", "warning")
            for group in groups_with_errors:
                print_panel(f"{group[0]} - {group[1]} - {group[2]}", "warning")

        # Write to a file log
        # publication timestamp groups without_errors with_errors
        with_errors = len(groups_with_errors)
        without_errors = num_groups - with_errors
        line = [post, datetime.now(), num_groups, without_errors, with_errors]

        with open(posts_folder_path / "log.csv", "a") as log_file:
            writer = csv.writer(log_file, delimiter=";")
            
            writer.writerow(line)

        exit_app()


@app.callback()
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
        ] = POST_FOLDER_PATH
):
    """
    Automate facebook posts.
    """
    posts_folder = Path(posts_folder_path)

    # Find available posts
    if not posts_folder.exists():
        print_panel(f"Folder {posts_folder_path} does not exist", "error")
    else:
        # Profile folder
        profile_folder = Path(posts_folder) / "profile"

        # If not exists, create it
        if not profile_folder.exists():
            profile_folder.mkdir()

        for file in posts_folder.iterdir():
            if file.is_dir() and file.name != "profile":
                available_posts.append(file.name)

        if not available_posts:
            print_panel(f"No posts found in {posts_folder_path}", "error")

        ctx.obj = {
            "chrome_binary_path": chrome_binary_path,
            "headless": headless,
            "posts_folder_path": posts_folder_path,
            "available_posts": available_posts
        }


if __name__ == "__main__":
    app()
