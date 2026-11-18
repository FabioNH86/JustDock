# JustDock — Server Installation

This guide sets up a JustDock server on Ubuntu (tested on recent releases shipping MariaDB 11.x).

Run the commands one at a time in a terminal (`Ctrl+Alt+T`) unless stated otherwise, and try to keep the same terminal session throughout so you stay in the expected directories.

## Contents

1. [Project layout](#1-project-layout)
2. [Getting the code](#2-getting-the-code)
3. [MariaDB](#3-mariadb)
4. [Python environment and dependencies](#4-python-environment-and-dependencies)
5. [Database](#5-database)
6. [Docking dependencies](#6-docking-dependencies)
7. [Docking scripts](#7-docking-scripts)
8. [Environment variables (optional)](#8-environment-variables-optional)
9. [Starting the server](#9-starting-the-server)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Project layout

Everything lives under `~/.local/src`:

```
~/.local/src/
├── justdock/              # project root
│   ├── jimag/             # Django web app (manage.py, tri.sh, requirements.txt, package.json)
│   └── jimag-scripts/     # docking pipeline scripts
├── adfr/ADFRsuite-1.0/    # ADFR suite
├── chimera/               # UCSF Chimera
├── p2rank_2.4/            # P2Rank
└── vina_1.2.5/            # AutoDock Vina
```

`jimag/` and `jimag-scripts/` must stay **sibling folders**: the startup script locates the docking scripts relative to the web app.

## 2. Getting the code

```bash
mkdir -p ~/.local/src
cd ~/.local/src
sudo apt install git
git clone <repository-url> justdock
```

## 3. MariaDB

```bash
sudo apt install mariadb-server
sudo systemctl enable --now mariadb
```

> **Note:** `mysql_secure_installation` no longer exists on recent Ubuntu versions, and its replacement (`mariadb-secure-installation`) is unnecessary on Debian/Ubuntu: the MariaDB `root` user already authenticates through the Unix socket (only `sudo` can log in as root). You can skip it.

## 4. Python environment and dependencies

```bash
cd ~/.local/src/justdock/jimag
sudo apt install python3-venv python3-dev default-libmysqlclient-dev build-essential pkg-config
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate

sudo apt install redis-server openjdk-17-jre-headless npm tmux
npm install
```

> **Java version:** P2Rank 2.4 only works with **Java 17**. Newer releases (e.g. the Java 25 installed by `default-jdk` on recent Ubuntu) make it fail with `Unsupported class file major version 69`. Java 17 can live alongside the system's default Java; [section 6](#p2rank-use-java-17) points P2Rank to it.

The JavaScript bundles in `static/` are already built. Rebuild them with `npx webpack` only if you modify the `.ts` sources.

## 5. Database

Open the MariaDB console as root. When asked for a password, just press **Enter**:

```bash
sudo mariadb -u root -p
```

```sql
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'adminpasswd';
GRANT ALL PRIVILEGES ON *.* TO 'admin'@'localhost';
quit;
```

Log in as the new user (password: `adminpasswd`) and create the database:

```bash
mariadb -u admin -p
```

```sql
CREATE DATABASE db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
quit;
```

Apply Django migrations:

```bash
cd ~/.local/src/justdock/jimag
source .venv/bin/activate
python3 manage.py makemigrations
python3 manage.py migrate
deactivate
```

> Use straight quotes (`'`) in SQL. Curly quotes (`‘ ’`) copied from word processors cause syntax errors.

## 6. Docking dependencies

If you don't have them yet, download the dependencies from:
<https://mega.nz/folder/1oEB0aAJ#OJM5KgGLa2-Ykfr8T2O8HA>

Go to your downloads folder (`~/Downloads`, or `~/Descargas` on a Spanish-language system) and extract the archive. MEGA may name it differently than `deps.zip`; check with `ls`:

```bash
cd ~/Downloads
ls
unzip deps.zip
cd deps
```

### ADFR suite

```bash
chmod +x ADFRsuite_Linux-x86_64_1.0_install
./ADFRsuite_Linux-x86_64_1.0_install
```

In the graphical installer:

1. Click **Next**.
2. Click **Browse…**, enter `/home/<your-user>/.local/src/adfr/ADFRsuite-1.0`, click **OK**, then **Next**.
3. Leave **academic install** selected and click **Next**.
4. Click **Finish**.

### UCSF Chimera

```bash
chmod +x chimera-1.16-linux_x86_64.bin
./chimera-1.16-linux_x86_64.bin
```

When asked for the install location, enter `/home/<your-user>/.local/src/chimera`. Press **Enter** on every remaining prompt, including the final one.

### P2Rank, Vina and Open Babel

```bash
tar xzvf p2rank_2.4.tar.gz
mv p2rank_2.4 ~/.local/src/
mv vina_1.2.5 ~/.local/src/
chmod +x ~/.local/src/vina_1.2.5/*
sudo apt install openbabel
```

### P2Rank: use Java 17

P2Rank 2.4 bundles Groovy 3.0.9, which cannot read class files from Java versions newer than 17. Make its launcher always use Java 17, without changing the system's default Java:

```bash
sed -i 's|^#JAVA_HOME="/opt/java8"|#JAVA_HOME="/opt/java8"\n# P2Rank 2.4 (Groovy 3.0.9) does not support Java > 17\nJAVA_HOME="${PRANK_JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}"|' ~/.local/src/p2rank_2.4/prank
```

If Java 17 is installed somewhere else, set `PRANK_JAVA_HOME` to its folder. Check that P2Rank runs:

```bash
cd ~/.local/src/p2rank_2.4
./prank predict -c ~/.local/src/justdock/jimag-scripts/configs/blind.groovy -f test_data/1fbl.pdb -o /tmp/prank_test
```

It should end with `finished successfully` and create `/tmp/prank_test/1fbl.pdb_predictions.csv`.

## 7. Docking scripts

Make the scripts executable and compile `max2pockets` for your machine:

```bash
cd ~/.local/src/justdock/jimag-scripts
chmod +x *.sh *.py *.awk sanitize setdirs
gcc -O2 -o max2pockets max2pockets.c -lm
```

> **Do not run `setdirs`.** It is a legacy helper for the standalone scripts: it rewrites every `*.sh` in the folder with `sed`, and its patterns also overwrite lines the web app depends on (for example the `--wd` option in `multi.sh`). The server does not need it; `tri.sh` sets all paths. If you do use it for standalone runs, pass the project folder as the first argument (`./setdirs /path/to/project`); otherwise it defaults to the `jimag-scripts/` folder itself.

## 8. Environment variables (optional)

The startup script (`tri.sh`) sets `HOMEDIR`, `PROJECTROOT` and `SCRIPTDIR` by itself, so this step is **not required** to run the server. Do it only if you want these variables available in your own terminal sessions.

Add them to your shell's config file: `~/.bashrc` for Bash or `~/.zshrc` for Zsh (check with `echo $SHELL`). Paste the whole block at once:

```bash
cat >> ~/.bashrc << 'EOF'
# jimag
export HOMEDIR=$HOME
export JUSTDOCK=$HOME/.local/src/justdock
export SCRIPTDIR=$JUSTDOCK/jimag-scripts
export PROJECTROOT=$JUSTDOCK/jimag
EOF
source ~/.bashrc
```

(Replace `~/.bashrc` with `~/.zshrc` in both lines if you use Zsh.) No reboot is needed.

## 9. Starting the server

Create a shortcut in your home folder and run it:

```bash
cd
ln -sf ~/.local/src/justdock/jimag/tri.sh inicio
chmod +x ~/.local/src/justdock/jimag/tri.sh
./inicio
```

The script starts the RQ worker, Django and Redis (port 6380) in a `tmux` session called `jimag` and attaches to it in the current terminal. If a graphical session is available, it also opens <http://localhost:8000> in the browser.

| Action | Command |
| --- | --- |
| Start / restart the server | `./inicio` (from your home folder) |
| Detach without stopping services | `Ctrl+B`, then `D` |
| Reattach to the running session | `tmux attach -t jimag` |
| Stop all services | `tmux kill-session -t jimag` |

Installation is complete when <http://localhost:8000> loads in the browser.

## 10. Troubleshooting

| Problem | Fix |
| --- | --- |
| `mysql_secure_installation: command not found` | Not needed; see [MariaDB](#3-mariadb). |
| `unzip: cannot find or open deps.zip` | Wrong folder or different file name. Look for it with `find ~ -iname "*.zip" -mmin -120`. |
| `gnome-terminal: command not found` | You are running an old `tri.sh`. Update to the current version, which uses `tmux` in the current terminal. |
| Stuck at a `->` prompt in MariaDB | The statement wasn't closed. Press `Ctrl+C`, then type `quit;`. |
| Docking jobs fail to find scripts | Make sure `jimag/` and `jimag-scripts/` are sibling folders. `./inicio` prints the `SCRIPTDIR` it is using. |
| P2Rank fails with `Unsupported class file major version 69` (or another number above 61) in `~/.local/src/p2rank_2.4/log/prank.log` | P2Rank is running with a Java newer than 17. Install `openjdk-17-jre-headless` and apply [P2Rank: use Java 17](#p2rank-use-java-17). |
| `/results/` returns *Internal Server Error* with `User has no profile` | Old code version. The current one creates each user's `Profile` automatically (on sign-up, when a job is created, and when results are opened), including for users created before the fix. No migration is needed. |
| Deleting a job returns *Internal Server Error* | Old code version. The current `delete_job` handles deleting your most recent or your only job, and returns `403` for jobs that don't exist or belong to another user. |
| `AttributeError: 'super' object has no attribute 'dicts'` (in `django/template/context.py`) | Django 5.0 is not compatible with Python 3.14. Upgrade Django inside `.venv` (`pip install "django>=5.2"`) or create the virtual environment with an older Python. |

### Where to find errors

| What failed | Where to look |
| --- | --- |
| Docking pipeline (scripts, Vina, Open Babel) | Top pane of the `jimag` tmux session (RQ worker), lines prefixed with `BASH_LOG:` |
| Web pages (HTTP 500 errors) | Bottom-left pane of the `jimag` tmux session (Django), or `jimag/script_output.log` |
| Pocket prediction | `~/.local/src/p2rank_2.4/log/prank.log` |
| A specific job's files | `jimag/media/user_<user-id>/job_<job-id>/` |
