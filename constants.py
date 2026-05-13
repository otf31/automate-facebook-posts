import os
import platform

from _version import __version__

OWNER = "otf31"
REPOSITORY_NAME = "autofbpost"
EMAIL = "otf31x@outlook.com"
REPOSITORY_URL = f"https://github.com/{OWNER}/{REPOSITORY_NAME}"
GITHUB_RELEASE_API = f"https://api.github.com/repos/{OWNER}/{REPOSITORY_NAME}/releases/latest"
APP_VERSION = __version__
WEBPAGE_URL = "https://autofbpost.sourceforge.net/"
API_URL = "https://automate-facebook-posts-back.onrender.com/"
FACEBOOK_URL = "https://www.facebook.com"
CHROME_BINARY_PATH = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if (platform.system()) == "Windows"
    else "/opt/google/chrome/google-chrome"
)
APP_NAME = "autofbpost"
CONFIG_FILE_PATH = "config.json"
HiSTORY_FILE_PATH = "log.csv"
DEFAULT_CONFIG = {
    "CHROME_BINARY_PATH": CHROME_BINARY_PATH,
    "POSTS_FOLDER_PATH": "",
    "HEADLESS": False,
}
SUPPORTED_FB_LANGUAGES = {"en": "English", "es": "Español"}
DEV_MODE = os.getenv("TEXTUAL_DEV") == "1"
