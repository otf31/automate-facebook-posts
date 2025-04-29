import platform
from typing import Literal

os = platform.system()

AUTHOR = "otf31"
EMAIL = "otf31.351663@gmail.com"
API_URL = "https://automate-facebook-posts-back.onrender.com/"
FACEBOOK_URL = "https://www.facebook.com"
CHROME_BINARY_PATH = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os == "Windows"
    else "/opt/google/chrome/google-chrome"
)
APP_NAME = "autofbpost"
CONFIG_FILE_PATH = "config.json"
HiSTORY_FILE_PATH = "log.csv"
CONFIG_KEYS_TYPES = Literal["CHROME_BINARY_PATH", "POSTS_FOLDER_PATH", "HEADLESS"]
DEFAULT_CONFIG = {
    "CHROME_BINARY_PATH": CHROME_BINARY_PATH,
    "POSTS_FOLDER_PATH": "",
    "HEADLESS": False,
}
SUPPORTED_FB_LANGUAGES = {"en": "English", "es": "Español"}
