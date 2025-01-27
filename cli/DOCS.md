# `autofbpost`

Automate facebook posts.

**Usage**:

```console
$ autofbpost [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--chrome-binary-path TEXT`: The Chrome binary path  [default: /opt/google/chrome/google-chrome]
* `--headless / --no-headless`: Run the browser in headless mode  [default: headless]
* `--posts-folder-path TEXT`: The folder containing the posts  [default: /home/otf31/Desktop/publication/]
* `--version`: Show the application version.
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `publish`: Publish posts.
* `id`: Get the unique device id
* `manual-mode`: Open a browser with the given user...

## `autofbpost publish`

Publish posts. The available values are the folders inside the posts folder where
the posts are stored. The post folder path is defined with the --posts-folder-path
option. This command also will check whether the user is logged in or not. If there
is not a valid Facebook session, then login process must be done manually using the
`manual-mode` command.

**Usage**:

```console
$ autofbpost publish [OPTIONS]
```

**Options**:

* `--post []`: The post. This is a required option, but if not provided, the CLI will prompt the user to enter the value. The available values are the folders (except profile) inside the posts folder where the posts are stored.  [required]
* `--help`: Show this message and exit.

## `autofbpost id`

Get the unique device id

**Usage**:

```console
$ autofbpost id [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `autofbpost manual-mode`

Open a browser with the given user directory (this command ignore headless option).
With this command you can perform manual actions in the browser like login into
your Facebook account, choose a profile, etc...
At the end, you can close the browser window and exit the command by pressing ENTER.

**Usage**:

```console
$ autofbpost manual-mode [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.
