import typer
from playwright.sync_api import sync_playwright

from common_functions import launch_browser, is_logged_in, print_panel

app = typer.Typer(no_args_is_help=True)


@app.command()
def login(
        ctx: typer.Context
):
    """
    Login into Facebook (this command ignore headless option).
    """
    # Force headful mode
    ctx.obj["headless"] = False

    with sync_playwright() as p:
        page = launch_browser(ctx, p)

        if is_logged_in(page):
            print_panel("You are already logged in", "error")

        print_panel(
            "Please, [blue]login manually into your Facebook account[/blue]")
        input("Press ENTER once you are logged in...")

        page.close()
