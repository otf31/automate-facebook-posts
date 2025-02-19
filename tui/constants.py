from typing import Literal

AUTHOR = "otf31"
EMAIL = "otf31.351663@gmail.com"
API_URL = "https://automate-facebook-posts-back.onrender.com/"
FACEBOOK_URL = "https://www.facebook.com"
CHROME_BINARY_PATH = "/opt/google/chrome/google-chrome"
APP_NAME = "autofbpost"
CONFIG_FILE = "config.json"
LOG_FILE = "log.csv"
CONFIG_KEYS_TYPES = Literal["CHROME_BINARY_PATH", "POSTS_FOLDER_PATH", "HEADLESS"]
DEFAULT_CONFIG = {
    "CHROME_BINARY_PATH": "/opt/google/chrome/google-chrome",
    "POSTS_FOLDER_PATH": "",
    "HEADLESS": False,
}
