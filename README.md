# AutoFBPost

**AutoFBPost** is a semi-automation tool with a text user interface (TUI) that makes posting to multiple Facebook groups
easy. Save time and effort by publishing to several groups with just a few clicks.

## 📋 Features

- ✅ **Automated publishing** to multiple Facebook groups
- 🎲 **Random selection** of descriptions from a predefined set
- 🖼️ **Automatic image upload** (JPG, JPEG, PNG)
- 🔍 **Filter system** to select specific groups
- ⏱️ **Random delays** between posts to avoid detection
- 📊 **Publication history** with statistics
- 🌐 **Multi-language support** (English and Spanish)
- 🔐 **Manual mode** for logging in and configuring your profile
- 🎨 **Modern text interface** built with Textual

## 📦 Requirements

- **Windows** or **Linux** operating system
- **Chromium based browser** installed on the system
- **Stable Internet connection**
- **Active Facebook account**

## 🚀 Installation

### Download the executable

Simply download the executable from the official website:

🌐 **Download**: https://autofbpost.sourceforge.net/

No additional installation or dependencies are required. Just download and run the executable file.

## ⚙️ Configuration

### First run

On first run, you can configure the parameters through the **Configuration** screen. Access it by:

- Pressing `c` from the main menu, or
- Clicking the "Configuration" option in the menu

You can configure the following parameters:

1. **Chromium-based browser binary path**: Path to your Chromium-based browser executable
    - Examples: Google Chrome, Microsoft Edge, Brave, Opera, etc.
    - Windows (Chrome): `C:\Program Files\Google\Chrome\Application\chrome.exe`
    - Windows (Edge): `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`
    - Linux (Chrome): `/opt/google/chrome/google-chrome` (or wherever your browser is installed)

2. **Posts folder path**: Path to the folder where your posts are stored

3. **Headless mode**: Enable/disable headless mode (no GUI)

After configuring the parameters, click the **Save** button to save your settings. The configuration will be used for
all subsequent runs.

### Folder structure

The project requires a specific folder structure:

```
posts_folder/
├── profile/             # Browser profile (created automatically)
├── groups.csv           # CSV file with group information
└── post_name_1/         # Post folder
    ├── images/          # Images to publish (JPG, JPEG, PNG)
    ├── descriptions/    # .txt files with descriptions (minimum 3)
    └── filters.txt      # Filters separated by commas
```

### `groups.csv` format

The CSV file must have the following format (delimiter: `;`):

```csv
Group Name;Group URL;Filters
Technology Group;https://www.facebook.com/groups/123456;technology,programming
Music Group;https://www.facebook.com/groups/789012;music,entertainment
```

**Columns:**

- **Column 1**: Group name
- **Column 2**: Complete Facebook group URL
- **Column 3**: Filters separated by commas (used to filter groups based on the post)

### `filters.txt` format

Simple text file with filters separated by commas:

```
technology,programming,python
```

### Description format

Each `.txt` file in the `descriptions/` folder should contain a complete description for the post. The application will
randomly select a description from these files.

## 🎮 Usage

### Run the application

Simply execute the downloaded executable file:

- **Windows**: Double-click the `.exe` file or run it from the command line
- **Linux**: Make it executable (`chmod +x autofbpost`) and run it (`./autofbpost`)

### Interface navigation

- **Publish**: Start the automated publishing process
- **Manual mode**: Open the browser for manual interaction (useful for logging in)
- **Id**: Show machine ID
- **Exit**: Exit the application

### Keyboard shortcuts

- `h`: Open history
- `c`: Open configuration
- `a`: About
- `Ctrl+Q`: Exit the application

### Publishing process

1. Select a post from the dropdown menu
2. The application will automatically validate:
    - Existence of the images folder
    - Minimum 3 description files
    - Valid groups file
    - Valid filters file
3. Click "Start" to begin
4. The application will:
    - Select a random description
    - Filter groups according to the specified filters
    - Publish to each group with random delays between posts
    - Show real-time progress
    - Record history upon completion

### Delays between posts

- **Every 5 groups**: Random delay between 115-148 seconds
- **Between normal groups**: Random delay between 60-75 seconds

These delays help avoid automatic detection by Facebook.

## 📁 Project structure

```
tui/
├── __init__.py
├── _version.py              # Application version
├── main.py                  # Main entry point
├── about.py                 # About screen
├── browser_utils.py         # Browser utilities
├── common_functions.py      # Common functions
├── configuration.py         # Configuration screen
├── constants.py             # Application constants
├── history.py               # History screen
├── machine_id.py            # Machine ID management
├── manual_mode.py           # Manual mode
├── publish.py               # Publishing logic
├── subscription.py
├── styles.tcss              # Textual styles
├── locales_fb/              # Facebook translations
│   ├── en.toml
│   └── es.toml
└── pyproject.toml           # Project configuration
```

## 🛠️ Technologies used

- **[Textual](https://textual.textualize.io/)**: TUI framework for Python
- **[Playwright](https://playwright.dev/python/)**: Browser automation
- **[httpx](https://www.python-httpx.org/)**: Async HTTP client
- **[fs](https://docs.pyfilesystem.org/)**: Virtual filesystem
- **[rtoml](https://github.com/sethmlarson/rtoml)**: TOML parser in Rust

## ⚠️ Warnings

- This tool is designed for personal and educational use
- Make sure to comply with Facebook's terms of service
- Excessive use may result in account restrictions
- Random delays are designed to minimize detection but don't guarantee complete protection
- Use this tool responsibly and ethically

## 🌍 Supported languages

The Facebook interface must be in one of the following languages:

- **English** (en)
- **Spanish** (es)

If your Facebook account is in another language, change the language in Facebook settings before using the application.

## 📝 History

Publication history is automatically saved in `log.csv` within the posts folder. It contains:

- Post name
- Date and time
- Total groups
- Successfully published groups
- Groups with errors

## 👤 Author

Developed by **@otf31**

- 📧 Email: otf31x@outlook.com
- 🌐 Aplication Web: https://autofbpost.sourceforge.net/

## Development

### Run in development mode

```shell
TEXTUAL_DEV=1 uv run main.py
```

With live editing CSS

```shell
TEXTUAL_DEV=1 uv run textual run main.py --dev
```

### Build executables

#### Linux

```shell
uv run nuitka --assume-yes-for-downloads --onefile --include-data-files=styles.tcss=styles.tcss --include-data-dir=locales_fb=locales_fb --linux-icon=./assets/autofbpost.ico --playwright-include-browser=none --output-filename=autofbpost main.py
```

#### Windows

```shell
uv run nuitka --assume-yes-for-downloads --onefile --include-data-files=styles.tcss=styles.tcss --include-data-dir=locales_fb=locales_fb --windows-icon-from-ico=./assets/autofbpost.ico --playwright-include-browser=none --output-filename=autofbpost main.py
```

## 🤝 Contributing

Contributions are welcome. Please:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Reporting issues

If you find any issues or have suggestions, please open an issue in the repository.

## 📚 Additional documentation

For more information, visit: https://autofbpost.sourceforge.net/

---

## LICENSE

This project is licensed under the GNU General Public License v3.0.