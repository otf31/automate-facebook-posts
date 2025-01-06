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

## Folders structure and files
### Folder structure
```shell
.
├── 1
│   ├── description.txt -> The description of the post
│   ├── filters.txt
│   └── images
│       ├── image1.jpeg
│       ├── image2.jpeg
│       ├── image3.jpeg
│       └── image4.jpeg
├── 2
│   ├── description.txt
│   ├── filters.txt
│   └── images
│       ├── image1.jpeg
│       └── image2.jpeg
├── groups.csv
└── log.csv
```

## Groups file
The groups file is a CSV file that contains the groups where the posts will be published.
The file must have the following columns:
- `group_name`: The name of the group
- `group_url`: The URL of the group
- `group_filters`: The filters to apply to the group (where to publish). The filters 
  are separated by commas. The content of this column will be compared with the 
  content of the `filters.txt` file in the post folder. If there is a match, then 
  the group will be selected to publish the post.

Example:

File: `groups.csv`
```csv
Group 1;https://www.facebook.com/groups/group1;filter1, filter2
```

File: `1/filters.txt`
```txt
filter2, filter4
```

In this case, the group `Group 1` will be selected to publish the post because the 
filters `filter2` is present in the `filters.txt` file.

## Log file
The log file is a CSV file that contains the information about the posts that have been published.
The file must have the following columns:
- `post`: The name of the folder where the post is stored
- `timestamp`: The timestamp when the post was published
- `groups_number`: The total number of groups
- `groups_submitted`: The groups where the post was submitted
- `groups_failed`: The groups where the post was not submitted

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
