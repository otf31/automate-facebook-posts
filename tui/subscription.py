import httpx
import machineid
from httpx import ConnectError, HTTPStatusError, ReadTimeout

from constants import API_URL


def get_device_id() -> str:
    """
    Get the device id.
    :return: The unique machine id.
    """
    return machineid.hashed_id()


async def get_subscription_status() -> (bool, str | None):
    """
    Get the subscription status.
    :return: A boolean indicating if the subscription is active.
    """
    # Get the machine id
    machine_id = get_device_id()

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{API_URL}check-subscription",
                params={"machine_id": machine_id},
                timeout=httpx.Timeout(70),
            )

            # Raise an exception if the status code is 4xx or 5xx
            r.raise_for_status()

            if r.status_code == 200:
                return True, None
    except HTTPStatusError as e:
        if e.response.status_code < 500:
            return False, "No active subscription"
        else:
            return (
                False,
                "An error occurred while checking the subscription status. Contact "
                "support",
            )
    except (ConnectError, ReadTimeout):
        return False, "Could not connect to the server."
