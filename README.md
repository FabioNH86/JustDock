# jimag — JustDock web server

jimag is the web front end of **JustDock**, a blind molecular docking server.
A user uploads a protein (receptor) and a small molecule (ligand). The server
predicts binding pockets on the protein, docks the ligand into the selected
pockets with AutoDock Vina, and shows the resulting poses and scores in a 3D
viewer in the browser.

For installation on a new machine, see [`../INSTALL.md`](../INSTALL.md).

## Contents

1. [How it works](#how-it-works)
2. [Docking pipeline](#docking-pipeline)
3. [Project layout](#project-layout)
4. [Starting and stopping the server](#starting-and-stopping-the-server)
5. [Local use](#local-use)
6. [Remote use (Tailscale Funnel)](#remote-use-tailscale-funnel)
7. [Security notes](#security-notes)
8. [Troubleshooting](#troubleshooting)

---

## How it works

The server is made of three processes, started together by `tri.sh` in a
`tmux` session called `jimag`:

```
 Browser ──HTTP──▶ Django (runserver, 127.0.0.1:8000)
                      │  stores users, jobs and results in MariaDB (database "db")
                      │  saves uploaded files to media/user_<id>/job_<id>/input/
                      │
                      └─ enqueues a job ──▶ Redis (port 6380) ──▶ RQ worker
                                                                   │
                                                                   └─ runs jimag-scripts/multi.sh
                                                                      (Open Babel, Chimera, P2Rank,
                                                                       ADFR suite, AutoDock Vina)
```

| Component | Role |
|---|---|
| **Django** (`manage.py runserver`) | Web pages, user accounts, job forms, results viewer. Apps: `core` (home, about), `users` (register, login), `jobs` (job submission and tasks), `dashboard` (results, downloads, job deletion). |
| **MariaDB** | Users, jobs (`created → queued → started → finished / failed`), proteins, ligands and dockings. |
| **Redis** on port 6380 | Job queue used by `django-rq`. |
| **RQ worker** (`manage.py rqworker`) | Runs `jobs.tasks.run_docking_script`, which calls the shell pipeline and writes each output line to the job's `progress` field, so the web page can show live progress. |
| **`jimag-scripts/`** | The docking pipeline itself (shell, AWK and Python scripts). |

A typical job, from the user's point of view:

1. Register or log in.
2. In **Jobs**, upload a receptor (`.pdb`) and a ligand (e.g. `.sdf`). Optionally
   choose chains and pockets, or let the server pick them.
3. Submit. The job is queued and its progress is shown while it runs.
4. In **Results**, browse each docking run, pocket and binding mode in the 3D
   viewer, and download the output files.

## Docking pipeline

`jobs/tasks.py` runs `jimag-scripts/multi.sh` twice per job, with the job's
folder (`media/user_<id>/job_<id>/`) as working directory (`--wd`):

**1. Pre-docking** (`--run_mode predock`), run once per job:

| Step | Script | Tools | Output |
|---|---|---|---|
| Clean receptor, keep the selected chains | `receptor_pre.sh` + `receptor.py` | Open Babel, UCSF Chimera | `receptor.pdb` |
| Predict pockets | `receptor_pre.sh` | P2Rank 2.4 (Java 17) | `receptor.pdb_predictions.csv` |
| 3D geometry and PDBQT for the ligand | `ligand.sh` | Open Babel, ADFR `prepare_ligand` | `ligand.mol2`, `ligand.pdbqt` |
| Add hydrogens, PDBQT for the receptor | `receptor_multi.sh` | ADFR `reduce`, `prepare_receptor` | `receptor.pdbqt` |
| Choose pockets (`--pockets`, `--max_pockets`, or the top-ranked one) | `multi.sh`, `max2pockets` | | `pockets` |

**2. Docking** (`--run_mode dock_only`), repeated for each docking run requested
in the form. Each run gets its own `docking_<id>/` folder with one
`pocket_<rank>/` subfolder per pocket:

| Step | Script | Tools | Output |
|---|---|---|---|
| Grid box around the pocket | `box_multi.sh` + `box_multi.awk` | | `box.txt` |
| Docking | `dock_multi.sh` | AutoDock Vina 1.2.5 | `modes.pdbqt`, `scores.txt` |
| Split poses | `multi.sh` | Open Babel | `mode_1.pdbqt`, `mode_2.pdbqt`, … |

`multi.sh` can also be run by hand, outside the web app (run
`multi.sh --help` for its options), which is useful for debugging a single
step.

## Project layout

```
~/.local/src/justdock/
├── INSTALL.md            installation guide
├── jimag/                Django project (this folder)
│   ├── manage.py
│   ├── tri.sh            starts Redis, Django and the RQ worker in tmux
│   ├── jimag/            settings.py, urls.py
│   ├── core/  users/  jobs/  dashboard/
│   ├── static/           built JS/CSS bundles (rebuild with `npx webpack`)
│   └── media/            per-user job folders (git-ignored)
└── jimag-scripts/        docking pipeline (multi.sh and its steps)
```

`jimag/` and `jimag-scripts/` must be sibling folders: `tri.sh` and
`settings.py` find the scripts relative to the web app (`SCRIPTDIR`). The
external tools live next to the project, in `~/.local/src/` (`adfr/`,
`chimera/`, `p2rank_2.4/`, `vina_1.2.5/`).

## Starting and stopping the server

After installation, start everything with the `inicio` shortcut created in
[INSTALL.md, section 9](../INSTALL.md#9-starting-the-server):

```bash
~/inicio          # same as ~/.local/src/justdock/jimag/tri.sh
```

`tri.sh` kills any previous `jimag` session and whatever is listening on ports
8000 and 6380, then starts three panes:

| Pane | Process |
|---|---|
| Top | RQ worker (docking logs, lines prefixed with `BASH_LOG:`) |
| Bottom left | Django on `127.0.0.1:8000` |
| Bottom right | Redis on port 6380 |

It then enables remote access if Tailscale is available (see below), opens
<http://localhost:8000> in the browser if there is a graphical session, and
attaches to the session.

| Action | Command |
|---|---|
| Start / restart | `~/inicio` |
| Detach, leaving the server running | `Ctrl+B`, then `D` |
| Reattach | `tmux attach -t jimag` |
| Stop all services | `tmux kill-session -t jimag` |

Code changes in the Django apps are picked up automatically by `runserver`.
Changes to `jobs/tasks.py` need a restart of the RQ worker (or simply
`~/inicio`). Changes to `jimag-scripts/` apply to the next job, with no
restart.

## Local use

Local use needs nothing beyond the installation: open
**<http://localhost:8000>** (or <http://127.0.0.1:8000>) on the machine that
runs the server.

- Django listens only on `127.0.0.1`, so the server is not reachable from
  other machines on the local network.
- `ALLOWED_HOSTS` in `jimag/settings.py` includes `localhost` and
  `127.0.0.1`, so local access keeps working whether or not remote access is
  enabled. (The IPv6 form `http://[::1]:8000` is not in the list; use
  `localhost` instead.)
- This is the recommended way to develop and test changes: edit the code, then
  reload the page or resubmit a job.

## Remote use (Tailscale Funnel)

To let people use the server from other machines, `tri.sh` publishes it with
[Tailscale Funnel](https://tailscale.com/kb/1223/funnel). Funnel forwards a
public HTTPS address to `localhost:8000`:

```
https://<machine-name>.<tailnet-name>.ts.net  ──▶  Tailscale  ──▶  http://localhost:8000
```

The address is public: anyone with the link can open it, without installing
Tailscale. The server itself still listens only on `127.0.0.1`. No ports are
opened on the router and no firewall changes are needed.

### Requirements (one-time setup)

1. Install Tailscale and log in:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
2. Allow your user to manage Tailscale without `sudo`, so that `tri.sh` can
   enable Funnel:
   ```bash
   sudo tailscale set --operator=$USER
   ```
3. Enable **HTTPS certificates** and **Funnel** for the tailnet in the
   Tailscale admin console. The first time you run `tailscale funnel`, it
   prints a link that does this.

### How it is enabled

When `~/inicio` runs, `tri.sh`:

1. Runs `tailscale funnel --bg 8000`. The setting persists in Tailscale, even
   after the `jimag` session stops.
2. Prints the public URL (`URL pública para compartir: https://…ts.net`) and
   shows it on the right of the tmux status bar.
3. If Tailscale is not installed, this step is skipped silently. If Funnel
   cannot be enabled, it prints a warning. In both cases the server starts
   normally for local use.

Django accepts these requests because `jimag/settings.py` contains:

```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.ts.net']
CSRF_TRUSTED_ORIGINS = ['https://*.ts.net']
```

`CSRF_TRUSTED_ORIGINS` is required: without it, every form submitted through
the HTTPS address (login, registration, job submission) fails with
*403 CSRF verification failed*.

### Useful commands

| Action | Command |
|---|---|
| Show the public URL and whether Funnel is on | `tailscale funnel status` |
| Turn remote access off (local use keeps working) | `tailscale funnel --https=443 off` |
| Turn it on again without restarting the server | `tailscale funnel --bg 8000` |

> **Tailnet-only access.** To share the server only with devices in your own
> tailnet, use `tailscale serve --bg 8000` instead of Funnel. The `.ts.net`
> settings above work for both.

## Security notes

The current settings are meant for development, but remote access exposes the
server to the internet. While Funnel is on:

- `DEBUG = True`: any error page shows full tracebacks, file paths and
  settings to the visitor. For longer public use, set `DEBUG = False` and
  serve static files (e.g. `collectstatic` and WhiteNoise).
- `SECRET_KEY` is the hard-coded `django-insecure-…` key, which is committed to
  git. Load it from an environment variable instead.
- Registration is open: anyone with the URL can create an account and submit
  jobs, which run on this machine's CPU.
- The database credentials in `settings.py` are the defaults from INSTALL.md.

Turn Funnel off (`tailscale funnel --https=443 off`) when remote access is not
needed.

## Troubleshooting

| Problem | Where to look / fix |
|---|---|
| A job ends as *failed* | Top pane of `tmux attach -t jimag`: the last `BASH_LOG:` lines show which step failed. The job's files are in `media/user_<id>/job_<id>/`. |
| HTTP 500 on a page | Bottom-left pane (Django), or `script_output.log`. |
| Pocket prediction fails | `~/.local/src/p2rank_2.4/log/prank.log`. P2Rank 2.4 needs Java 17 (see INSTALL.md). |
| `AssertionError: ligand.mol2 does't exist` | ADFR's `prepare_ligand4.py` keeps only the file name of `-l`. `ligand.sh` runs it from inside the job folder to account for this; make sure you have the current `ligand.sh`. |
| `400 Bad Request` on the `.ts.net` address | `ALLOWED_HOSTS` is missing `.ts.net`. |
| `403 CSRF verification failed` on the `.ts.net` address | `CSRF_TRUSTED_ORIGINS` is missing `https://*.ts.net`. |
| `AVISO: no se pudo activar Tailscale Funnel` | Run `tailscale funnel --bg 8000` by hand to see the reason (not logged in, Funnel not enabled for the tailnet, or no operator permission). |

More installation-related problems are covered in
[INSTALL.md, section 10](../INSTALL.md#10-troubleshooting).
