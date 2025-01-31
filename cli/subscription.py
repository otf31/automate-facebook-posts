import httpx
import machineid
import typer
from httpx import ConnectError, HTTPStatusError
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
    # Get the machine id
    machine_id = get_device_id()

    try:
        r = httpx.get(
            f"{API_URL}check-subscription",
            params={"machine_id": machine_id},
            timeout=httpx.Timeout(70),
        )

        # Raise an exception if the status code is 4xx or 5xx
        r.raise_for_status()

        if r.status_code == 200:
            return True
    except HTTPStatusError as e:
        if e.response.status_code < 500:
            print_panel(
                f"Your subscription is not active. Please contact support.",
                title="No active subscription",
                msg_type="warning",
            )
        else:
            print_panel(
                f"An error occurred while checking the subscription status. Contact "
                f"support",
                title="Subscription error",
                msg_type="warning",
            )

        return False
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
