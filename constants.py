from fs import open_fs

FACEBOOK_URL = "https://www.facebook.com"
CHROME_BINARY_PATH = "/opt/google/chrome/google-chrome"

with open_fs("~/") as home_fs:
    POSTS_FOLDER_PATH = home_fs.getsyspath("Desktop/publication/")
