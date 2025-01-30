import httpx
import machineid
import typer
from httpx import ConnectError
from rich.status import Status

from common_functions import print_panel
from constants import API_URL


def get_device_id() -> str:
    """
    Get the device id.
    :return: The unique machine id.
    """
    return machineid.hashed_id()


def get_subscription_status() -> bool | None:
    """
    Get the subscription status.
    :return: A boolean indicating if the subscription is active.
    """
    machine_id = get_device_id()

    try:
        r = httpx.get(
            f"{API_URL}check-subscription",
            params={"machine_id": machine_id},
            timeout=httpx.Timeout(70),
        )

        if r.status_code >= 400:
            print_panel(
                f"Your subscription is not active. Please contact support.",
                title="No active subscription",
                msg_type="warning",
            )

            return False

        if r.status_code == 200:
            return True
    except ConnectError:
        print_panel(
            f"Could not connect to the server.",
            title="Connection error",
            msg_type="error",
        )


def check_active_subscription() -> None:
    """
    Check if the subscription is active. If not, exit the application.
    """
    with Status("Checking subscription status..."):
        has_active_subscription = get_subscription_status()

    if not has_active_subscription:
        raise typer.Exit()
