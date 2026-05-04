# API Linter — VS Code Extension

A Visual Studio Code extension that lints OpenAPI specification files (`.yaml`) against a set of rules using the [api-linter-opensource](https://github.com/bahag/api-linter-opensource) backend. Violations are surfaced as inline diagnostics directly in the editor, with red highlights for errors and orange highlights for warnings.

---

## Features

- Lints `.yaml` API spec files automatically on **save** and on **change**
- Runs on demand via the **"Linter"** button in the status bar
- Inline line highlights:
  - 🔴 **Red** — rule violations with severity `ERROR`
  - 🟠 **Orange** — rule violations with severity `WARNING`
- Falls back to **Docker** automatically if the native `linting` binary is not installed

---

## Requirements

You need **one** of the following to run the linter:

### Option A — Native binary (recommended)

Install the `linting` CLI and make sure it is on your `$PATH`:

```bash
# Check if it is already available
which linting
```

Refer to the [api-linter-opensource releases](https://github.com/bahag/api-linter-opensource) for installation instructions.

### Option B — Docker (automatic fallback)

If the native binary is not found, the extension will automatically run the linter via Docker:

```bash
docker run --platform linux/amd64 --rm \
  -v $(pwd):/spec \
  ghcr.io/bahag/api-linter-opensource:latest \
  linting -s /spec/your-api-spec.yaml -r /rules.json -o json
```

Make sure the **Docker daemon is running** and the image can be pulled from `ghcr.io`.

---

## Installation

1. Clone or download this repository.
2. Open the folder in VS Code.
3. Run the extension in a new Extension Development Host window:
   - Press `F5`, or
   - Open the **Run and Debug** panel and select **Run Extension**.

To package and install the extension permanently:

```bash
npm install -g @vscode/vsce
vsce package          # produces api-linter-0.0.1.vsix
code --install-extension api-linter-0.0.1.vsix
```

---

## Usage

1. Open a `.yaml` API specification file in VS Code.
2. The linter runs automatically when you **save** or **edit** the file.
3. To trigger linting manually, click the **"Linter"** button in the status bar (bottom-left).
4. Violations are shown as:
   - Coloured line highlights in the editor (red / orange)
   - Entries in the **Problems** panel (`View → Problems` or `Ctrl+Shift+M` / `Cmd+Shift+M`)

---

## Rules

Custom linting rules are loaded from `data/rules.json` inside the extension directory. Edit that file to add, remove, or modify the rules applied during linting.

---

## Extension Settings

This extension does not currently contribute any VS Code settings. Configuration is done by editing `data/rules.json`.

---

## Known Issues

- Only `.yaml` files are linted; `.json` OpenAPI specs are not yet supported.
- When using the Docker fallback, the first run may be slow due to image pulling.
- The `-it` (interactive TTY) flag is intentionally omitted in the Docker command to allow programmatic use inside the extension.

---

## Release Notes

### 0.0.1

Initial release — inline error/warning highlighting with native binary and Docker fallback support.
