import typer
from playwright.sync_api import sync_playwright
from rich.prompt import Prompt

from common_functions import launch_browser, is_logged_in, print_panel

cli = typer.Typer(no_args_is_help=True)


@cli.command()
def login(
        ctx: typer.Context
) -> None:
    """
    Login into Facebook (this command ignore headless option).
    This command will open a browser window and let you login
    manually into your Facebook account.
    You can select the profile you want to use to publish as well.
    :param ctx: The Typer context.
    """
    # Force headful mode
    ctx.obj["headless"] = False

    with sync_playwright() as p:
        page = launch_browser(ctx, p)

        if is_logged_in(page):
            print_panel("You are already logged in", msg_type="error")

        print_panel(
            "Please, [blue]login manually into your Facebook account[/blue]")

        Prompt.ask("Press Enter when you are done...")

        page.close()
