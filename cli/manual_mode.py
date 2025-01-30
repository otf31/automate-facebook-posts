import typer
from playwright.sync_api import sync_playwright
from rich.prompt import Prompt

from browser_utils import launch_browser, navigate
from constants import FACEBOOK_URL
from subscription import check_active_subscription

cli = typer.Typer(no_args_is_help=True)


@cli.command()
def manual_mode(ctx: typer.Context) -> None:
    """
    Open a browser with the given user directory (this command ignore headless option).
    With this command you can perform manual actions in the browser like login into
    your Facebook account, choose a profile, etc...
    At the end, you can close the browser window and exit the command by pressing ENTER.
    """
    check_active_subscription()

    # Force headful mode
    ctx.obj["headless"] = False

    with sync_playwright() as p:
        page = launch_browser(ctx, p)

        navigate(page, FACEBOOK_URL)

        Prompt.ask("Press ENTER to close the browser window and exit...")
