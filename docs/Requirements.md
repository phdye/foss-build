# Requirements for `foss-build` Implementation

## Overview

The `foss-build` utility is a command-line tool designed to automate the building, testing, and installation of software packages. It utilizes standard build tools available on Unix-like operating systems, such as `autoconf` and `make`, and manages log files and installation directories efficiently. This document outlines the functional requirements for any implementation of `foss-build`, ensuring identical functionality to the original script.

## Usage

```
USAGE: foss-build [options] [commands]

Unattended build and install of FOSS package using the standard sequence:
    autoconf, configure, make, make test, make install

Unless commands are present, in which case it runs each command in the
order specified by the user. This is to handle resolving build errors
without having to start over from scratch.

Must be executed in the project source root.

Options:
  --large    Switches install prefix to /opt/stow/<project-name>-<version>.
             If the working directory is the root of an unpacked release
             tar with a release version suffix.  The stow prefix is
             generated using "/opt/stow/$(basename ${PWD})".

             Creates .stow trigger so subsequent runs are stowed automatically.

  --no-sudo  Disables the use of sudo during the installation step.

Commands:
  autoconf   Runs autoconf to generate the configure if configure.ac is present.
  configure  Runs the ./configure script with the specified prefix.
  build      Compiles the source code using make with parallel jobs.
  test       Runs tests to verify the build using make test.
  install    Installs the built software to the specified prefix.
             Installation done using sudo unless `--no-sudo` specified.
```

## Functional Requirements

### 1. Input Handling

- **Command-Line Arguments:**
  - The tool must accept various command-line arguments to control its behavior:
    - `--large`: This flag sets the installation prefix to `/opt/stow/$(basename ${PWD})` with the expectation that the root of the project being built is an unpacked release tar with the version in the folder name.

      It creates a `./.stow` file to remember this choice for future runs. Once the `.stow` file exists, subsequent uses of `--large` do not alter the behavior further, ensuring consistency.

      To revert to the default behavior, the ./.store file must be removed.

    - `--no-sudo`: This flag configures the tool to install software without using `sudo`. If this argument is used, the tool must create a `./.no-sudo` trigger file to remember this choice for future installations.

      To revert to the default behavior, the ./.no-sudo file must be removed.

    - **Positional Commands**: The tool must accept these positional commands that specify which build steps to execute and in what order.  Only used when recovering from a failed run.

      <u>Recognized commands include</u>:

      - `autoconf`: Runs  `autoconf`, if and only if configure.ac exists.
      - `configure`: Executes the `./configure` script with the specified prefix.
      - `build`: Compiles the software using `make`.
      - `test`: Runs `make test` to validate the build.
      - `install`: Installs the compiled software.

  - **Validation of Arguments:**
    - The tool must validate the command-line arguments to ensure they are recognized and in the correct format. If an unrecognized argument or incorrect format is detected, the tool should display an appropriate error message and exit with a non-zero status code.

- **Environment Variables:**
  - The tool must support the following environment variables to alter default settings:
    - `PARALLEL`: Specifies the number of parallel jobs for the `make` command.  [Default: `8`]
    - `PREFIX`: Defines the installation prefix.  [Default: `/usr/local`]
  - The tool must allow these environment variables to be overridden by command-line arguments, when applicable.

### 2. Processing Workflow

- **Sequential Steps:**
  - Unless specific commands are provided via the command line, the tool must perform the following steps in sequence:
    0. **Autoconf**: Run `autoconf` if a `configure.ac` file is present in the current directory.
          *It is step 0 since roughly half of time it wasn't needed when this was first implemented.*
    1. **Configure**: Execute `./configure` with the specified prefix (`--prefix=${PREFIX}`).
    2. **Build**: Compile the software using `make -j ${PARALLEL}`
    3. **Test**: Run `make -j ${PARALLEL} test` to validate the build.
    4. **Install**: Install the compiled software using `sudo make -j ${PARALLEL} install`.  Unless `--no-sudo` is specified or the `.no-sudo` trigger file is present, then it simply uses `make -j ${PARALLEL} install`. 

- **Conditional Logic:**
  - The tool must check for the existence of specific trigger files and adjust its behavior accordingly:
    - `.stow`: If this file exists in the current directory, the tool should set the installation prefix to a stow-managed directory.
    - `.no-sudo`: If this file exists, the tool should perform installations without using `sudo`, even if `--no-sudo` is not explicitly passed as an argument.

### 3. Output and Logging

- **Log Files:**
  - The tool must generate log files for each build step, storing both raw and processed logs in a structured directory hierarchy under a `log` directory:
    - **Directory Structure**: Logs must be stored in subdirectories named after each step :

      ```
      ./log
      ├── 0.autoconf
      ├── 1.configure
      ├── 2.build
      ├── 3.test
      └── 4.install
      ```

    - **File Naming**: Each step's directory should contain a `raw` file (containing unfiltered output) and a `txt` file (containing filtered output).

- **Console Output:**
  - The tool must passthrough all command output to the conosole, in addition to logging it.

### 4. Error Handling and Exit Codes

- **Standard Exit Codes:**
  - The tool manages steps according to the POSIX exit code convention:
    - An exit code of `0` indicates success and the tool will then proceed to the step.
    - Any non-zero exit code indicates an error and the tool will stop and return the non-zero exit status to the calling process, most likely a user shell.

- **Error Logging:**
  - All output to STDOUT and STDERR and captured in a single stream multiplexed to the console and the raw log file.   Whether such includes what the user needs to debug the issue is out of scope for this simple tool.

### 5. Output Filtering

- **Log Processing Rules:**
  - The complete output of each command is logged to `./log/n.<command>/raw`.
  - On most systems, this will include quite easy to read ANSI colorization to better organize the large amounts of data.  And frankly, this is extremely useful.  However, for detailed searching and other uses, plain text would be better, i.e. `./log/n.<command>/txt`.
  - Applies filtering rules convert `raw` to `txt` :

    | **To Remove :**           | **Sed Expression**                      | **Regex sub(e, '', s)**            |
    | ------------------------- | --------------------------------------- | ---------------------------------- |
    | **ANSI Escape Codes**     | `s/\x1b\[[0-9;]*[a-zA-Z]//g`            | `\x1b\[[0-9;]*[a-zA-Z]`            |
    | **Xterm Titles**          | `s/\x1b]0;.*\x07//g`                    | `\x1b]0;.*\x07`                    |
    | **Control Characters**    | `s/[\x01-\x09\x0B\x0C\x0E-\x1F\x7F]//g` | `[\x01-\x09\x0B\x0C\x0E-\x1F\x7F]` |
    | **Redundant Empty Lines** | `/^$/N;/^\n$/D`                         | `(r'\n+(?=\n)', '\n', s)`          |

### 6. Valid and Invalid Inputs

- **Valid Inputs:**
  - Recognized command-line arguments (`--large`, `--no-sudo`, positional commands).
  - Supported environment variables (`PARALLEL`, `PREFIX`).
  - Properly formatted configuration files and scripts (`configure.ac`, `Makefile`).

- **Invalid Inputs:**
  - Unrecognized command-line arguments or improperly formatted inputs should result in an error message and a non-zero exit code.
  - Missing or incorrect configuration files (`configure.ac`, `Makefile`) should result in the relevant build step failing with an appropriate error message.

## Constraints

- The tool should be implemented using a modern programming language that supports:
  - File and directory operations.
  - Process management and execution.
  - Regular expressions for output filtering.

- The implementation must be self-contained, relying only on standard system utilities and the build tools (`autoconf`, `make`) specified. It must not assume the availability of bespoke tools beyond those described.
