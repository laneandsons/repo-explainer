# Cloud Agents

What an unattended Claude Code cloud session (claude.ai/code, "Claude Code on the web") starts
with, and what this repo has to commit so a session can pick up a ticket and work it with nobody
watching.

Researched 2026-09-09 against Anthropic's official docs. Every claim below carries a source URL and
a confidence marker. Read [Confidence and gaps](#confidence-and-gaps) before you rely on anything
here.

Confidence markers used throughout:

- **[Documented]** — stated outright in an official Anthropic doc page. Cited.
- **[Inferred]** — follows from two documented facts, but no doc says it directly. Verify before
  betting on it.
- **[Unknown]** — could not find an authoritative answer. Do not guess.

---

## 1. The short version

A cloud session is a **fresh Ubuntu 24.04 x86_64 virtual machine (VM)**, per session, with your
repo cloned into it and a fat toolchain already installed. It has network access through a proxy,
restricted to an allowlist by default. It can run your tests. It pushes a branch to GitHub and can
open a pull request (PR).

The two things people get wrong:

1. **Nothing from your laptop comes along.** Not `~/.claude/CLAUDE.md`, not `~/.claude/skills/`,
   not `~/.claude/plugins/`, not your local MCP servers. Only what is committed to the repo, plus
   things attached to your **claude.ai account**.
2. **The setup script is not a file in the repo.** It lives in your cloud *environment* settings on
   claude.ai. The repo-side equivalent is a `SessionStart` hook. Section 5 covers the difference.

---

## 2. What the container has preinstalled

**[Documented]** Each Anthropic-hosted session gets a fresh VM running **Ubuntu 24.04 on x86_64**,
regardless of your own OS and CPU architecture.
Source: <https://code.claude.com/docs/en/cloud-environments> (§ What's available in cloud sessions)

The preinstalled tool table, verbatim from that page:

| Category      | Included                                                                   |
| :------------ | :------------------------------------------------------------------------- |
| **Python**    | Python 3.x with pip, poetry, uv, black, mypy, pytest, ruff                 |
| **Node.js**   | 20, 21, and 22, with npm, yarn, pnpm, bun¹, eslint, prettier, chromedriver |
| **Ruby**      | 3.1, 3.2, 3.3 with gem, bundler, rbenv                                     |
| **PHP**       | 8.3 with Composer                                                          |
| **Java**      | OpenJDK 21 with Maven and Gradle                                           |
| **Go**        | Go with module support                                                     |
| **Rust**      | rustc and cargo                                                            |
| **C/C++**     | GCC, Clang, cmake, ninja, conan                                            |
| **Docker**    | docker, dockerd, docker compose                                            |
| **Databases** | PostgreSQL 16, Redis 7.0                                                   |
| **Utilities** | git, gh, jq, yq, ripgrep, tmux, vim, nano                                  |

¹ Bun is installed but has known proxy compatibility problems when fetching packages.

So, directly answering the questions asked:

- **`uv` — present.** [Documented], in the Python row above.
- **`gh` — present and usable without `gh auth login`.** [Documented]. See section 3 for how the
  authentication actually works, because it is unusual.
- **Node — 20, 21, 22.** [Documented]. Installed at `/opt/node20`, `/opt/node21`, `/opt/node22`,
  with **22 on `PATH` by default**. To use another version, prepend e.g. `/opt/node20/bin` to
  `PATH`.
- **Python version — [Unknown].** The docs say only "Python 3.x". They do not name a minor version.
  This matters for this repo: `pyproject.toml` declares `requires-python = ">=3.14"`, and there is
  no documented guarantee the VM's Python satisfies that. See section 9 for the concrete risk.
- **.NET and anything else not in the table — not installed.** [Documented] explicitly: "Toolchains
  outside this list, such as the .NET SDK, aren't pre-installed even when their package registries
  are on the default allowlist."

**[Documented]** A shell command named `check-tools` is installed on the session VM and prints the
versions of most tools in that table. It is a shell command, not a slash command. You cannot run it
yourself — you don't get a shell into the VM — so you ask Claude to run it. For tools it doesn't
report (Ruby, PHP, bun, PostgreSQL, Redis) ask for the tool's own version command, e.g.
`psql --version`.
Source: <https://code.claude.com/docs/en/cloud-environments> (§ Installed tools)

**Resource limits [Documented]**, described as approximate and subject to change:

- 4 vCPUs
- 16 GB RAM
- 30 GB disk

"The VM may stop tasks that need significantly more memory, such as large build jobs or
memory-intensive tests."
Source: <https://code.claude.com/docs/en/cloud-environments> (§ Resource limits)

**[Documented]** You cannot replace the base image: "Replacing the base image entirely isn't
supported yet." You can only install on top of it with a setup script, or run your own image as a
container alongside Claude via `docker compose`.
Source: <https://code.claude.com/docs/en/cloud-environments> (§ Limitations in cloud sessions)

---

## 3. Network access

**[Documented]** Yes, there is network access, and yes it is restricted. Every environment picks
exactly one of four **access levels**:

| Level       | Outbound connections                                                     |
| :---------- | :----------------------------------------------------------------------- |
| **None**    | No outbound network access through the session's network                 |
| **Trusted** | Allowlisted domains only: package registries, GitHub, cloud SDKs         |
| **Full**    | Any domain                                                               |
| **Custom**  | Your own allowlist, optionally including the defaults                    |

**Trusted is the default.** The `Default` environment that onboarding creates uses Trusted and
carries no other configuration — no environment variables, no setup script.
Source: <https://code.claude.com/docs/en/cloud-environments> (§ Access levels, § The Default environment)

### The three domains you asked about

All three are reachable on the default **Trusted** level:

- **PyPI — reachable.** [Documented]. The default allowlist's "Python package managers" group
  contains `pypi.org`, `www.pypi.org`, `files.pythonhosted.org`, `pythonhosted.org`,
  `test.pypi.org`, `pypi.python.org`.
- **`raw.githubusercontent.com` — reachable.** [Documented]. It is in the "Version control" group,
  alongside `github.com`, `api.github.com`, `codeload.github.com`,
  `objects.githubusercontent.com`, `release-assets.githubusercontent.com`, and others.
- **`api.anthropic.com` — reachable, and reachable even at access level None.** [Documented]. It is
  in the "Anthropic services" group, and separately: "The Anthropic API, for Claude Code's own
  requests, even at **None**". The docs note the consequence plainly: "When running with network
  access disabled, Claude Code can still communicate with the Anthropic API, which may allow data
  to exit the VM."

Source: <https://code.claude.com/docs/en/cloud-environments> (§ Default allowed domains, § Access levels)
Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ Security and isolation)

### Four paths that bypass the access level entirely

**[Documented]** Regardless of the level you set, sessions can still reach:

1. GitHub, through its separate proxy (section 4)
2. MCP connectors you enabled, because that traffic goes through Anthropic's servers rather than
   the session's network
3. The hosts listed on the environment's API credentials
4. The Anthropic API

Source: <https://code.claude.com/docs/en/cloud-environments> (§ Access levels)

### The security proxy

**[Documented]** All outbound traffic from an Anthropic-hosted session passes through an
HTTP/HTTPS security proxy that does malicious-request protection, rate limiting, content filtering,
and DNS-level audit logging of requested hostnames. Blocked requests fail with `403` and the
response header `x-deny-reason: host_not_allowed`.
Source: <https://code.claude.com/docs/en/cloud-environments> (§ Security proxy)
Source: <https://code.claude.com/docs/en/routines> (§ Environments and network access)

**[Documented]** Some package managers do not work correctly through this proxy. **Bun is the named
example.** If a cloud session needs to install JavaScript packages, prefer npm/pnpm/yarn.
Source: <https://code.claude.com/docs/en/cloud-environments> (§ Limitations in cloud sessions)

---

## 4. Bootstrap: clone, branch, and pull request

### Clone

**[Documented]** On task submission the flow is:

1. Clone the repository to an Anthropic-managed VM, and run the setup script if configured.
2. Configure network access from the environment's access level.
3. Claude works — reads code, edits, runs tests.
4. When Claude reaches a stopping point, it **pushes its branch to GitHub**.

The session does not close when the branch is pushed; PR creation and further edits happen in the
same conversation.
Source: <https://code.claude.com/docs/en/web-quickstart> (§ How sessions run)

**[Documented]** Sessions always start from a **fresh clone**. Multiple repositories can be
attached to one session.

### Which branch it starts on

**[Documented]** Two different answers depending on how the session started:

- **From the web UI:** you pick the repository and the branch. Each repository row has a branch
  selector; change it to start from a feature branch instead of the default.
  Source: <https://code.claude.com/docs/en/web-quickstart> (§ Start a task)
- **From `claude --cloud` in the terminal:** "The cloud VM clones your current directory's GitHub
  remote at your current branch, not your local checkout, so push first if you have local commits."
  Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ From terminal to web)
- **From a routine (scheduled/API/GitHub-triggered run):** "Claude starts from the repository's
  default branch unless your prompt specifies otherwise."
  Source: <https://code.claude.com/docs/en/routines> (§ Repositories and branch permissions)

### Where it pushes

**[Documented]** For routines: "Claude pushes its work to branches prefixed with `claude/`, which
are always accepted." When a prompt directs Claude to push elsewhere, Claude Code checks the push
first and **rejects** it if the branch is protected on GitHub, if someone else has an open PR from
that branch, or if the branch carries commits authored by someone other than you.
Source: <https://code.claude.com/docs/en/routines> (§ Repositories and branch permissions)

**[Documented]** Independently, the GitHub proxy enforces: "`git push` works only against the
session's current working branch; cloning, fetching, and PR operations work normally."
Source: <https://code.claude.com/docs/en/cloud-environments> (§ GitHub proxy)

**[Unknown]** Whether the `claude/` branch prefix also applies to ordinary (non-routine) web
sessions. The routines page states it; the web pages do not repeat it.

### Opening the pull request

Three routes, all documented:

- **Human clicks a button.** In the diff view, **Create PR** opens it as a full PR, a draft, or
  jumps to GitHub's compose page with a generated title and description.
  Source: <https://code.claude.com/docs/en/web-quickstart> (§ Review and iterate)
- **You ask Claude, and Claude runs `gh pr create`.** [Documented] "You can create pull requests by
  asking Claude directly… Claude Code links the session to the PR when Claude creates it with
  `gh pr create` or `glab mr create`." `gh` is preinstalled and pre-authenticated via the proxy.
  Source: <https://code.claude.com/docs/en/common-workflows>
- **Built-in GitHub tools.** [Documented] Cloud sessions include built-in GitHub tools that let
  Claude "read issues, list pull requests, fetch diffs, and post comments without any setup."
  Note the list: **PR creation is not among the operations named for the built-in tools** — that
  path goes through `gh`.
  Source: <https://code.claude.com/docs/en/cloud-environments> (§ Work with GitHub issues and pull requests)

**This is the key fact for unattended ticket work:** Claude can read an issue and open a PR itself,
with no human present, using the built-in GitHub tools plus `gh`.

### How GitHub authentication works (it is not a normal token)

**[Documented]** All GitHub operations go through a dedicated proxy that keeps your real GitHub
credentials **outside** the session VM. Inside the VM, the git client uses a scoped credential that
the proxy verifies and swaps for your real token on the way out.

Consequences you must design around:

- **`gh` works without `gh auth login`.** [Documented]
- **`echo $GH_TOKEN` prints the literal string `proxy-injected`** when the proxy is handling auth.
  [Documented] "a script that reads `GITHUB_TOKEN` directly gets the placeholder, not a usable
  token." **Do not write repo scripts that read `GITHUB_TOKEN` and hand it to a raw HTTP client.**
  Shell out to `gh` instead.
- **GraphQL is heavily restricted.** [Documented] The proxy "serves only a pinned set of GraphQL
  operations for pull-request workflows." Everything else on the GraphQL endpoint gets a `403`
  saying `This GraphQL query is not enabled for this session`, naming the REST fallback
  `gh api repos/{owner}/{repo}/...`. **This applies even if you supply your own `GH_TOKEN`.**
  Claude cannot reach GitHub APIs that exist only in GraphQL — **GitHub Projects v2 is called out
  by name as unreachable.**
- **Repository scope.** [Documented] "GitHub API and release-asset requests reach only repositories
  attached to the session, so a setup script that downloads release assets from an unattached
  repository gets a 403."

Source: <https://code.claude.com/docs/en/cloud-environments> (§ GitHub proxy, § Work with GitHub issues and pull requests)

### Two ways to connect GitHub

**[Documented]**

| Method | How it works | Best for |
| :--- | :--- | :--- |
| **GitHub App** | Authorize the Claude GitHub App during web onboarding | Browser onboarding; teams that want Auto-fix |
| **`/web-setup`** | Run `/web-setup` in your terminal to sync your local `gh` CLI token to your Claude account | Developers who already use `gh` |

Important caveat, [Documented]: with either method **a cloud session can access any repository the
connecting GitHub account can see**, not just repos the App is installed on. Installing the App
enables PR webhooks (needed for Auto-fix and GitHub-event routine triggers); it is not a
session-level access control.

**[Documented]** If `/web-setup` warns your `gh` token lacks the `workflow` scope, pushes that
change GitHub Actions workflow files can be rejected. Fix with `gh auth refresh -s workflow`.

Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ GitHub authentication options)
Source: <https://code.claude.com/docs/en/web-quickstart> (§ Connect from your terminal)

### Session identity, for traceability

**[Documented]** The session can read its own ID from `CLAUDE_CODE_REMOTE_SESSION_ID`. Commits
Claude creates in a cloud session carry a `Claude-Session: <url>` git trailer, and PR bodies include
the session URL on its own line (requires v2.1.179+). Turn both off with
`attribution.sessionUrl: false` (v2.1.182+).

To build the URL yourself, the documented command is:

```bash
echo "https://claude.ai/code/${CLAUDE_CODE_REMOTE_SESSION_ID/#cse_/session_}"
```

Source: <https://code.claude.com/docs/en/cloud-environments> (§ Link output back to the session)

---

## 5. The setup hook — the important structural answer

**There is no repo file that a cloud session runs as a setup script.** This is the answer to the
"devcontainer `postCreateCommand` equivalent" question, and it is a two-part answer.

### Part 1: the setup script (account-scoped, not in the repo)

**[Documented]** A setup script is a Bash script that runs when a new cloud session starts, **before
Claude Code launches**. It is entered into the **Setup script** field of the environment dialog at
claude.ai/code — reached via the cloud icon in the row above the message box. There is no settings
page or direct URL for that selector, and **no committed file path**. For Team/Enterprise shared
environments an Owner sets it on the **Cloud environments** admin page.

- **Runs as root on Ubuntu 24.04**, so `apt install` and language package managers work.
- Documented example:

  ```bash
  #!/bin/bash
  apt update && apt install -y shellcheck
  ```

Three hard constraints:

1. **Exit zero.** A non-zero exit means the session fails to start. Append `|| true` to
   non-critical commands.
2. **Finish within roughly five minutes**, so the environment cache can build. Run independent
   installs in parallel with `&` and `wait`.
3. **Needs network access for installs.** Trusted covers npm, PyPI, RubyGems, crates.io. `None`
   blocks them all.

Source: <https://code.claude.com/docs/en/cloud-environments> (§ Setup scripts, § Script requirements, § Configure your environment)

**Environment caching [Documented]:** the setup script runs the **first** time you start a session
in an environment. Anthropic then snapshots the filesystem and reuses that snapshot for later
sessions, which **skip the setup script step**. The cache stores files only, not running processes —
installed packages and pulled Docker images carry over, a started database does not. The script
re-runs when you change the setup script or the allowed network hosts, and when the cache expires
after **roughly seven days**. Resuming an existing session never re-runs it.
Source: <https://code.claude.com/docs/en/cloud-environments> (§ Environment caching)

### Part 2: the SessionStart hook (this *is* in the repo)

**[Documented]** The repo-committable equivalent is a `SessionStart` hook in
**`.claude/settings.json`**. It runs **after** Claude Code launches, on **every** session including
resumed ones, and in **both** local and cloud sessions.

Documented shape, verbatim:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/scripts/install_pkgs.sh"
          }
        ]
      }
    ]
  }
}
```

And the documented pattern for making it cloud-only — the script checks the `CLAUDE_CODE_REMOTE`
environment variable, which is `"true"` in a cloud session VM and never `"true"` locally:

```bash
#!/bin/bash

if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

npm install
pip install -r requirements.txt
exit 0
```

`$CLAUDE_PROJECT_DIR` resolves to the repository root, so the hook finds the script regardless of
the session's working directory.

Source: <https://code.claude.com/docs/en/cloud-environments> (§ Install dependencies with a SessionStart hook)

### Which to use

**[Documented]** table, condensed:

|                     | Setup script                                    | SessionStart hook                                |
| :------------------ | :---------------------------------------------- | :----------------------------------------------- |
| **Configured in**   | Environment dialog on claude.ai (not the repo)  | Repo's `.claude/settings.json`                   |
| **When it runs**    | Before Claude Code launches; skipped when cached | After Claude Code launches; every session        |
| **Where it runs**   | Cloud sessions only                             | Local and cloud                                  |
| **Use it for**      | Toolchains and CLI tools not preinstalled       | Project setup that should run everywhere (`npm install`) |

Caveats on SessionStart hooks in the cloud [Documented]:

- No cloud-only scoping built in — use the `CLAUDE_CODE_REMOTE` check.
- Needs network access; fails at level `None`.
- Subject to the security proxy, so Bun-based installs may fail.
- Adds startup latency on **every** session, unlike setup scripts which are cached. Check whether
  dependencies are already present before reinstalling.

**[Documented]** Hooks in your user-level `~/.claude/settings.json` do **not** reach the cloud.

---

## 6. Running tests

**[Documented]** Yes. "Claude runs tests as part of working on a task. Ask for it in your prompt,
like 'fix the failing tests in `tests/`' or 'run pytest after each change.' Test runners that come
with the pre-installed toolchains, like pytest and cargo test, work without additional setup. A
runner your project declares as a dependency, like jest, installs with your dependencies."
Source: <https://code.claude.com/docs/en/cloud-environments> (§ Run tests)

**[Documented]** You do not get a shell into the session VM. Claude runs every command for you, so
phrase everything as a request in the prompt.

**Services [Documented]:** PostgreSQL 16 and Redis 7.0 are preinstalled but **not running**. The
documented start commands are `service postgresql start` and `service redis-server start`. Docker is
available; `docker compose up` works, and Docker Hub is on the Trusted allowlist. Because the
environment cache stores files but not processes, a `docker compose pull` or `docker compose build`
in the setup script persists the images but **not** the running stack — containers must be started
per session.
Source: <https://code.claude.com/docs/en/cloud-environments> (§ Start services, § Environment caching)

### Limits that constrain a test run

| Limit | Value | Confidence |
| :--- | :--- | :--- |
| vCPUs | 4 | [Documented] |
| RAM | 16 GB | [Documented] |
| Disk | 30 GB | [Documented] |
| Setup script runtime | ~5 minutes | [Documented] |
| Environment cache lifetime | ~7 days | [Documented] |
| Individual command / test timeout | — | **[Unknown]** |
| Maximum session duration | — | **[Unknown]** |
| Idle timeout before VM reclaim | "a period of inactivity" — no number given | **[Unknown]** |

**[Documented]** on idle expiry: "Cloud sessions stop after a period of inactivity and the session's
VM is reclaimed. On the web, the session is marked expired in the session list." Reopening the
session provisions a fresh VM with the conversation history restored, but **background work that was
still running when the VM was reclaimed — subagents and shell commands — is not restored.**
Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ Environment expired)

**[Documented]** Closing the browser tab does **not** stop the session. It keeps running until
Claude finishes the current task, then idles.
Source: <https://code.claude.com/docs/en/web-quickstart> (§ Session keeps running after closing the tab)

---

## 7. Parallel sessions

**[Documented]** Parallelism is a headline use case: "run several independent tasks at once, each in
its own session and branch, without managing multiple worktrees." And: "Each task gets its own
session and its own branch, so you don't need to wait for one to finish before starting another."
Source: <https://code.claude.com/docs/en/web-quickstart>

Three ways to launch several against the same repo:

1. **Web UI** — submit multiple tasks from claude.ai/code. Each becomes its own session/branch.
2. **CLI** — each `claude --cloud` invocation creates its own independent session. The documented
   example:

   ```bash
   claude --cloud "Fix the flaky test in auth.spec.ts"
   claude --cloud "Update the API documentation"
   claude --cloud "Refactor the logger to use structured output"
   ```

   Monitor them all with `/tasks` in the CLI.
   Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ Tips for cloud tasks)
3. **Pre-filled URLs**, for wiring a "work this ticket" button into an issue tracker. Query
   parameters on claude.ai/code: `prompt` (alias `q`), `prompt_url`, `repositories` (alias `repo`,
   comma-separated `owner/repo` slugs), `environment`. URL-encode each value. Documented example:

   ```text
   https://claude.ai/code?prompt=Fix%20the%20login%20bug&repositories=acme/webapp
   ```

   Source: <https://code.claude.com/docs/en/web-quickstart> (§ Pre-fill sessions)

### The limits on parallelism

**[Documented]** "Claude Code on the web shares rate limits with all other Claude and Claude Code
usage within your account. Running multiple tasks in parallel consumes more rate limits
proportionately. **There is no separate compute charge for the cloud VM.**"
Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ Limitations)

**[Unknown]** There is **no documented hard cap on the number of concurrent cloud sessions.** The
only stated constraint is your account's shared rate limit. Do not assume a specific number.

**[Documented]** For routines specifically there *are* caps: a daily cap on routine runs per
account (visible at claude.ai/code/routines or claude.ai/settings/usage), and during the research
preview, **per-routine and per-account hourly caps on GitHub webhook events** — events beyond the
limit are dropped until the window resets. One-off scheduled runs do not count against the daily cap.
Source: <https://code.claude.com/docs/en/routines> (§ Usage and limits, § Add a GitHub trigger)

**[Documented]** Session creation can simply fail: "`Session creation failed`… Claude Code could not
allocate a VM for the session… Retry after a minute, as capacity is provisioned on demand." Anything
that launches sessions in bulk must handle this.
Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ Session creation failed)

---

## 8. Skills, plugins, and configuration — what carries over

This is the table the docs publish, reproduced in full because it is the single most load-bearing
fact for repo setup. **[Documented]**, from
<https://code.claude.com/docs/en/cloud-environments> (§ What carries over from your setup):

| Thing | Available in cloud sessions? | Why |
| :--- | :--- | :--- |
| Repo's `CLAUDE.md` | **Yes** | Part of the clone |
| Repo's `.claude/settings.json` hooks | **Yes** | Part of the clone |
| Repo's `.mcp.json` MCP servers | **Yes** | Part of the clone |
| Repo's `.claude/rules/` | **Yes** | Part of the clone |
| Repo's `.claude/skills/`, `.claude/agents/`, `.claude/commands/` | **Yes** | Part of the clone |
| Plugins declared in the repo's `.claude/settings.json` | **Yes** | Installed at session start from the declared marketplace; needs network access to reach the marketplace source |
| Organization server-managed settings | **Yes** | Fetched from Anthropic's servers at session start |
| Your user `~/.claude/CLAUDE.md` | **No** | Lives on your machine, not in the repo |
| Your user `~/.claude/skills/`, `~/.claude/agents/`, `~/.claude/commands/` | **No** | Commit them to the repo's `.claude/` instead. Cloud sessions do automatically load skills you enable on claude.ai |
| Plugins enabled only in your user settings | **No** | User-scoped `enabledPlugins` lives in `~/.claude/settings.json`. Declare them in the repo's `.claude/settings.json`, or enable them for your claude.ai account so they load as synced plugins |
| MCP servers added with `claude mcp add` at local or user scope | **No** | Those write `~/.claude.json`. Use `claude mcp add --scope project`, which writes the repo's `.mcp.json`, and commit it |
| Transport variables in the repo's `settings.json` `env` block (`NODE_EXTRA_CA_CERTS`, mTLS client cert vars) | **No** | The hosting environment manages the API connection; Claude Code ignores these keys and notes each in the debug log |
| API keys/tokens for services Claude calls | Pro and Max only, as **API credentials** | The key never reaches the session; the agent proxy attaches it after the request leaves the VM |
| Interactive auth like AWS SSO | **No** | Requires browser login, which can't run in a cloud session |

The docs' own one-line summary: **"To make your own configuration available in cloud sessions,
commit it to the repo."**

### Skills specifically

**[Documented]** Skill locations and where each loads:

| Location | Path | Loads in cloud sessions? |
| :--- | :--- | :--- |
| Personal | `~/.claude/skills/<name>/SKILL.md` | **No** |
| Project | `.claude/skills/<name>/SKILL.md` | **Yes** (part of the clone) |
| Nested | `<subdir>/.claude/skills/<name>/SKILL.md` | Yes, for sessions in or below `<subdir>` |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Wherever the plugin is enabled |
| claude.ai account | Enabled in claude.ai settings | **Yes** — cloud and Cowork sessions |

Source: <https://code.claude.com/docs/en/skills>

**So: for this repo's skills to be available to a cloud session, they must be committed under
`.claude/skills/`.** This repo already has a `.claude/skills` directory, which is the right place.

### Plugins specifically — "synced plugins"

**[Documented]** Synced plugins are plugins enabled for your **claude.ai account**. Claude Code
downloads them automatically in Cowork and cloud sessions into `~/.claude/plugins/synced/` **in the
session's own environment**, and loads them as `<name>@synced`. They:

- involve no marketplace and no install record
- load **only** in Cowork/cloud sessions, **not** in your own terminal
- appear in `claude plugin list` under "Synced from claude.ai"
- were loaded as `<name>@inline` before v2.1.239

To exclude one from a specific project, commit this to `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "<name>@synced": false
  }
}
```

Note a wrinkle: `enabledPlugins` is read from managed settings, `--settings`, and **user** settings —
**project and local `.claude/settings.json` are ignored for `enabledPlugins` as of v2.1.207+**,
though the disable-a-synced-plugin recipe above is documented as a committed project file. These two
statements are in tension; treat the committed-disable recipe as the documented intent and verify
before relying on it.

Source: <https://code.claude.com/docs/en/plugins-reference> (§ Synced plugins, § enabledPlugins)

**Your local `~/.claude/plugins/cache/…` plugins (e.g. `mattpocock-skills`) do not reach a cloud
session.** [Documented, by the "plugins enabled only in your user settings: No" row]. The two
supported routes are: declare the plugin and its marketplace in the repo's committed
`.claude/settings.json`, or enable it for the claude.ai account so it arrives as a synced plugin.

### Slash commands that don't work in the cloud

**[Documented]** Cloud sessions support built-in commands that produce text output. Commands that
only run in the terminal interface — **`/plugin`, `/resume`** — are unavailable. `/clear` is
unavailable (start a new session instead). `/compact` and `/context` work. Picker-style commands
take an argument instead: `/model sonnet`, `/effort`, `/fast`, `/color`, `/rename` (v2.1.205+).
`/config` on the web opens settings rather than setting a value, and text after it is ignored —
**"To change settings for a cloud session, use environment variables or commit settings files to the
repository."** `/schedule` is unavailable inside a cloud session.
Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ Manage context)
Source: <https://code.claude.com/docs/en/routines> (§ Troubleshooting)

**[Documented]** Subagents work normally, and **subagents defined in the repo's `.claude/agents/`
are picked up automatically**. Agent teams are off by default and enabled with
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in environment variables.
Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ Manage context)

---

## 9. Fully unattended ticket work

### Permission modes

**[Documented]** Cloud sessions offer three modes, chosen at creation and changeable while running:

- **Auto** — a classifier reviews Claude's actions instead of asking you. Appears when your
  organization allows auto mode and the model supports it.
- **Accept edits** — Claude makes changes and pushes a branch without stopping for approval.
- **Plan** — Claude proposes an approach and waits for approval before editing.

**Manual and Bypass permissions are not offered in cloud sessions.**
Source: <https://code.claude.com/docs/en/web-quickstart> (§ Choose a permission mode)

For genuinely unattended work you want **Accept edits** or **Auto**.

### Routines — the "pick up a ticket with no human present" mechanism

**[Documented]** A routine is a saved configuration — prompt, repositories, connectors,
environment — with one or more triggers: **Scheduled** (min interval one hour), **API** (HTTP POST
to a per-routine `/fire` endpoint with a bearer token), and **GitHub events** (pull request and
release events only, with filters on author, title, body, base/head branch, labels, draft, merged).

Crucially: **"Routines run autonomously as full Claude Code cloud sessions: there is no
permission-mode picker and no approval prompts during a run."** The session can run shell commands,
use skills committed to the cloned repository, and call any connectors you include.

Routines are available on Pro, Max, Team, and Enterprise plans. Managed at
claude.ai/code/routines or with `/schedule` in the CLI.

Source: <https://code.claude.com/docs/en/routines>

Two things to know before designing around routines:

- **GitHub *issue* events are not a supported trigger.** [Documented] The supported event table
  lists only **Pull request** and **Release**. An issue-driven workflow must poll on a schedule, or
  be fired by an external system through the API trigger.
- **Fire text is deliberately untrusted.** [Documented] The optional `text` field in the `/fire`
  body arrives wrapped in a `<routine-fire-payload>` block labelled as untrusted data, with an
  instruction not to follow instructions inside it unless the routine's own prompt says to.
  **The routine's saved prompt must explicitly opt in**, e.g. "Investigate the alert described in
  the routine-fire-payload block" — otherwise the text is inert context.
- **A green run status means the session started and exited without an infrastructure error.**
  [Documented] It does **not** mean the task succeeded. Blocked network requests, missing connector
  tools, and task failures all surface in the transcript, not the status indicator.

### Auto-fix pull requests

**[Documented]** Claude can watch a PR and respond automatically to CI failures and review
comments, pushing a fix when one is clear and asking when a comment is ambiguous. Requires the
Claude GitHub App installed on the repository. Turn it on from the CI status bar in a web session,
with `/autofix-pr` from the terminal while on the PR's branch, from mobile, or by pasting a PR URL.

Two warnings, both documented:

- **GitHub emits no webhook when the base branch advances into a merge conflict**, so auto-fix
  cannot react to conflicts. Open the session and ask Claude to rebase.
- **Claude's replies to review threads post under your GitHub account** (labelled as coming from
  Claude Code). If your repo uses `issue_comment`-triggered automation such as Atlantis or Terraform
  Cloud, Claude can trigger it. Review that before enabling.

Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ Auto-fix pull requests)

### Blockers that stop cloud sessions entirely

**[Documented]**

- **Zero Data Retention organizations cannot use cloud sessions or `/web-setup` at all.**
- **Organization IP allowlisting breaks every Anthropic-hosted cloud session** with an
  authentication error, because sessions call the Anthropic API from Anthropic infrastructure, not
  your network. Same for Code Review and routines on Anthropic-hosted environments. Anthropic
  support can exempt Anthropic-hosted services.
- **Third-party providers are unsupported.** `--cloud` and `--teleport` are unavailable when Claude
  Code is configured for Amazon Bedrock, Google Cloud's Agent Platform, or similar. An LLM gateway
  configured only through `ANTHROPIC_BASE_URL` does not count as a third-party provider.
- **The org policy `allow_remote_sessions` must be on.**
- **GitLab, Bitbucket, and other non-GitHub remotes** can be sent as a local bundle via `--cloud`,
  but the session **cannot push results back**. Repository cloning and PR creation require GitHub
  (or GitHub Enterprise Server on Team/Enterprise plans).

Source: <https://code.claude.com/docs/en/claude-code-on-the-web> (§ Limitations, § Send follow-ups from the CLI)

---

## 10. Checklist for this repo

What `repo-explainer` should commit so a cloud session can work a ticket unattended. Items marked
[Documented] follow directly from a cited fact above.

- [x] **`CLAUDE.md` at the repo root** — already present, and it carries over. [Documented]
- [x] **`.claude/skills/`** — already present. This is the only way this repo's own skills reach a
      cloud session. [Documented]
- [ ] **`.claude/agents/`** for any subagents the workflow depends on — picked up automatically.
      [Documented]
- [ ] **`.mcp.json`** (via `claude mcp add --scope project`) for any MCP server the workflow needs.
      A `claude mcp add` at default or user scope will **not** be there. [Documented]
- [ ] **`.claude/settings.json`** with a `SessionStart` hook if dependencies must be installed on
      every session — plus the `CLAUDE_CODE_REMOTE` guard so it no-ops locally. [Documented]
- [ ] **Declare any needed plugins in the repo's `.claude/settings.json`**, or enable them for the
      claude.ai account. `~/.claude/plugins/` does not travel. [Documented]
- [ ] **`docs/agents/issue-tracker.md` conventions must be reachable via `gh` REST, not GraphQL.**
      This repo's tracker is GitHub Issues driven by `gh`. Issue read/comment via `gh` works
      (REST). **GitHub Projects v2 does not**, because it is GraphQL-only and the proxy blocks it.
      [Documented]
- [ ] **Never read `$GITHUB_TOKEN` in a committed script** — in a cloud session it is the literal
      string `proxy-injected`. Shell out to `gh`. [Documented]

### The Python-version risk, stated plainly

This repo declares `requires-python = ">=3.14"` in `pyproject.toml`. The cloud VM's Python is
documented only as "Python 3.x" — **[Unknown]** whether it satisfies that. Two consequences:

- **[Inferred]** If the VM's Python is older than 3.14, `uv sync` / `uv run` will try to fetch a
  matching interpreter. `uv` downloads standalone Python builds from GitHub **release assets** of a
  repository that is not the session's attached repository. The docs state: "GitHub API and
  release-asset requests reach only repositories attached to the session, so a setup script that
  downloads release assets from an unattached repository gets a 403." **This suggests
  `uv python install` will fail with a 403 in a cloud session.** This is an inference from two
  documented facts, not a documented statement about `uv`. **Verify it with one throwaway cloud
  session before designing around it** — ask Claude to run `python3 --version`, `uv --version`, and
  `uv python install 3.14` and report what happens.
- If it does fail, the documented workaround is a **setup script** on the cloud environment that
  installs the interpreter another way (e.g. the deadsnakes PPA or building from source), keeping
  the whole script under the ~5 minute budget. The result is cached for ~7 days.

---

## Confidence and gaps

### Answered with high confidence, from primary sources

- Ubuntu 24.04 / x86_64; the full preinstalled tool table; `uv`, `gh`, `pytest`, `ruff` all present;
  Node 20/21/22 at `/opt/nodeNN` with 22 on PATH.
- 4 vCPU / 16 GB RAM / 30 GB disk.
- Four network access levels, Trusted as default; PyPI, `raw.githubusercontent.com`, and
  `api.anthropic.com` all reachable on Trusted; `api.anthropic.com` reachable even at None.
- The GitHub proxy model: real credentials outside the VM, `GH_TOKEN` reads `proxy-injected`,
  GraphQL restricted to a pinned PR set, Projects v2 unreachable.
- Setup script is environment-scoped on claude.ai with no repo file; must exit zero; ~5 min budget;
  cached ~7 days.
- `SessionStart` hook in `.claude/settings.json` is the repo-committable equivalent, with the
  `CLAUDE_CODE_REMOTE` guard.
- Tests run; PostgreSQL/Redis installed but not started; Docker available.
- Exactly what carries over from local vs. repo vs. claude.ai account.
- Routines as the unattended trigger mechanism, with GitHub triggers limited to PR and Release
  events.

### Could NOT find an authoritative answer

1. **The exact Python minor version on the VM.** Docs say "Python 3.x" and nothing more. The only
   documented way to learn it is to ask a running session to run `check-tools` or `python3
   --version`. This is a real blocker for a repo pinned to `>=3.14`.
2. **Maximum session duration.** No number anywhere.
3. **Idle timeout before the VM is reclaimed.** Documented as "a period of inactivity" — no value.
4. **Per-command / per-Bash-tool timeout in cloud sessions.** Not documented for the cloud
   specifically.
5. **A hard cap on concurrent cloud sessions.** None documented. Only "shares rate limits with all
   other Claude and Claude Code usage" plus on-demand VM capacity that can fail allocation.
6. **Whether the `claude/` branch prefix applies to ordinary web sessions**, or only to routine
   runs. Only the routines page states it.
7. **Whether `uv python install` works through the proxy.** Inferred to fail (403 on unattached-repo
   release assets), but not documented either way. Needs one empirical check.
8. **Whether the built-in GitHub tools can create a PR**, or whether PR creation always goes through
   `gh`. The built-in tool list names read-issues, list-PRs, fetch-diffs, post-comments — creation
   is absent from that list, and `gh pr create` is documented separately.
9. **The tension in `enabledPlugins` scoping.** The plugins reference says project and local
   settings are ignored for `enabledPlugins` (v2.1.207+), yet documents disabling a synced plugin
   via a committed project `.claude/settings.json`. Unresolved.

### How to close gaps 1, 7, and 8 cheaply

Start one throwaway cloud session against this repo in **Plan** mode and ask it to run and report:
`check-tools`, `python3 --version`, `uv --version`, `uv python install 3.14`, `echo $GH_TOKEN`,
`env | grep CLAUDE_CODE`, and `gh pr create --help`. That single session answers five of the nine
open items empirically. (Per the research brief, this document's author did not launch one.)

## Sources

All URLs fetched 2026-09-09.

- <https://code.claude.com/docs/en/claude-code-on-the-web>
- <https://code.claude.com/docs/en/cloud-environments>
- <https://code.claude.com/docs/en/web-quickstart>
- <https://code.claude.com/docs/en/sandbox-environments>
- <https://code.claude.com/docs/en/routines>
- <https://code.claude.com/docs/en/skills>
- <https://code.claude.com/docs/en/plugins-reference>
- <https://code.claude.com/docs/en/common-workflows>
- <https://code.claude.com/docs/llms.txt> (documentation index)
