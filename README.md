# Auto Facebook Post
AutoFbPost is a CLI tool the helps you to post on Facebook automatically.
The aim of this project is to automate the process of posting on Facebook groups.

## Tech stack
- Python 3
- Selenium
- Typer
- Pyperclip

## Features
The CLI app comes with the following features:
- Post on Facebook groups

## Usage

### Publish posts
```shell
./autofbpost publish
Select a post (1, 2, 3, 4): 1
```
The available options are the folders inside the posts folder.

This command also will check whether the user is logged in or not. If there is not a
valid Facebook session, then that login process must be done manually.

After ther user is logged in and select the facebook profile to publish the posts, the user needs to press `ENTER` in the console to start the publication process.

## CLI arguments, options and commands
### Options
```shell
--chrome-binary-path TEXT The Chrome binary path
--chrome-driver-path TEXT The Chrome driver path
--chrome-config-path TEXT The Chrome config path
--chrome-profile TEXT The Chrome profile
--headless --no-headless Run the browser in headless mode [default: no-headless]
--posts-folder-path TEXT The folder containing the posts
```

### Commands
1. `publish`: Publish post a post. This command always is executed in heaful mode.
   #### Options
    ```shell
    This is a required option, but if not provided, the CLI will prompt the user to enter the value.
    The available values are the folders inside the posts folder where the posts are stored.
    The post folder path is defined with the --posts-folder-path option.
    --post The post [default: None] [required]
    ```

2. `login`: Login to Facebook manually. This command always is executed in headful mode.

## Build
```shell
python -m nuitka --onefile main.py --output-filename=autofbpost
```

## Resources
- https://docs.python.org/3/library/pathlib.html#corresponding-tools
- https://rich.readthedocs.io/en/latest/panel.html
- Wait an element to disappear: https://stackoverflow.com/questions/73414090/how-to-wait-for-multiple-loading-element-to-disappear-using-selenium
