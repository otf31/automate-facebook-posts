import machineid


def get_device_id() -> str:
    """
    Get the device id.
    :return: The unique machine id.
    """
    return machineid.hashed_id()
