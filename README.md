# 🔍 BAHAG API Linter

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://ghcr.io/bahag/api-linter-opensource)

A comprehensive quality assurance tool for OpenAPI specifications that ensures your APIs meet industry standards and organizational guidelines.

## 📚 Table of Contents

- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [📖 Usage](#-usage)
- [⚙️ Configuration](#️-configuration)
  - [Metadata Configuration](#-metadata-configuration)
  - [Rules Configuration](#-rules-configuration)
  - [Validation Checks](#-validation-checks)
  - [Exception Handling](#️-exception-handling)
- [📝 Output Examples](#-output-examples)
- [🧩 VS Code Extension](#-vs-code-extension)
  - [Prerequisites](#prerequisites)
  - [Downloading the Extension](#downloading-the-vs-code-extension)
  - [Installing the Extension](#installing-the-extension-in-vs-code)
  - [Using the Extension](#using-the-extension)
- [🏗️ Development](#️-development)
  - [Local Development Setup](#local-development-setup)
  - [Project Structure](#project-structure)
  - [Adding New Rules](#adding-new-rules)
- [🚀 Deployment & Versioning](#-deployment--versioning)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🆘 Support & Contact](#-support--contact)
- [🔗 Related Tools](#-related-tools)

## ✨ Features

- **🚀 Quality Assurance**: Automatically validates OpenAPI specifications against best practices
- **📋 Compliance Checking**: Ensures adherence to [Bauhaus' RESTful Guidelines](https://guideline.api.bauhaus/)
- **⚡ Early Feedback**: Provides immediate validation during API design phase
- **🎯 Consistency**: Maintains uniform look-and-feel across all APIs
- **🐳 Docker Ready**: Easy deployment with containerized solution
- **📊 Multiple Output Formats**: Supports JSON and YAML output formats
- **🔧 Configurable Rules**: Customizable linting rules via JSON configuration

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Login to GitHub Container Registry:**
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin
   ```

2. **Pull the latest image:**
   ```bash
   docker pull ghcr.io/bahag/api-linter-opensource:latest
   ```

3. **Run the linter:**
   ```bash
   docker run --platform linux/amd64 -it -v $(pwd):/spec \
     ghcr.io/bahag/api-linter-opensource:latest \
     linting -s /spec/your-api-spec.yml -r /rules.json -o json
   ```

### Local Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install yq (YAML processor):**
   ```bash
   # macOS
   brew install yq
   
   # Linux
   wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
   chmod +x /usr/local/bin/yq
   ```

3. **Run locally:**
   ```bash
   python local_dev/linter.py -s your-api-spec.yml -r rules.json -o json
   ```

## 📖 Usage

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--spec` | `-s` | Path to OpenAPI specification file | Required |
| `--rule` | `-r` | Path to rules configuration file | Required |
| `--output` | `-o` | Output format (`json` or `yaml`) | `json` |

### Example Usage

```bash
# Basic usage
linting -s api-spec.yaml -r rules.json

# With custom output format
linting -s api-spec.yaml -r rules.json -o yaml

# Using Docker with volume mount
docker run -v $(pwd):/workspace \
  ghcr.io/bahag/api-linter-opensource:latest \
  linting -s /workspace/api-spec.yaml -r /workspace/rules.json
```

## ⚙️ Configuration

The linter uses a `rules.json` file to define validation rules and metadata extraction requirements.

### Basic Structure

```json
{
    "metadata": ["openapi", "info.version", "info.title"],
    "rules": [
        {
            "id": "B101",
            "description": "Provide API specification using OpenAPI",
            "severity": "ERROR",
            "specification-type": "OPENAPI",
            "specification-version": "ALL",
            "paths": [...]
        }
    ]
}
```

### 📊 Metadata Configuration

Metadata defines which YAML paths to extract from your OpenAPI specification:

```json
{
    "metadata": [
        "openapi",
        "info.version", 
        "info.title",
        "info.x-audience",
        "info.contact.name"
    ]
}
```

**Example OpenAPI file:**
```yaml
openapi: 3.0.0
info:
    version: 1.2.3
    title: My API
    x-audience: internal
    contact:
        name: API Team
```

### 📏 Rules Configuration

Rules define the validation logic applied to your OpenAPI specification:

#### Rule Structure
```json
{
    "id": "B101",
    "description": "Provide API specification using OpenAPI",
    "severity": "ERROR",
    "specification-type": "OPENAPI", 
    "specification-version": "ALL",
    "paths": [
        {
            "required_path": "openapi",
            "message": "OpenAPI version not specified",
            "checks": [
                {
                    "name": "gte",
                    "value": "3.0.0", 
                    "message": "OpenAPI version must be >= 3.0.0"
                }
            ]
        }
    ]
}
```

#### Severity Levels
- **ERROR**: Critical issues that must be fixed
- **WARN**: Recommendations and best practices

#### Path Types

| Type | Description | Example |
|------|-------------|---------|
| `required_path` | Validates specific YAML paths | `"required_path": "info.version"` |
| `key_name` | Validates key presence | `"key_name": "title"` |
| `properties` | Validates all properties | `"properties": "*"` |
### 🔍 Validation Checks

#### Basic Checks
```json
{
    "name": "gte",
    "value": "3.0.0",
    "message": "Version must be >= 3.0.0"
}
```

```json
{
    "name": "pattern", 
    "value": "^\\d+\\.\\d+\\.\\d+$",
    "message": "Must follow semantic versioning"
}
```

```json
{
    "name": "allowed_values",
    "value": ["internal", "external", "partner"],
    "message": "Must be one of the allowed values"
}
```

```json
{
    "name": "string_match",
    "value": "application/json",
    "message": "Must match exact string"
}
```

#### Property-Specific Checks
```json
{
    "name": "is_array",
    "value": true,
    "message": "Array names must be plural"
}
```

```json
{
    "name": "is_date_time", 
    "value": ["[a-z]*_at$", "valid_from", "valid_until"],
    "message": "Date/time properties must end with _at, _from, or _until"
}
```

#### Key Validation Checks
```json
{
    "name": "check_keys_value",
    "value": {
        "value": "query",
        "required_node": "name", 
        "node_requirement": "^[a-z_][a-z_0-9]*$"
    },
    "message": "Query parameters must follow snake_case"
}
```

```json
{
    "name": "check_keys_list",
    "value": ["200", "201", "202", "204"],
    "message": "Must use standard HTTP status codes"
}
```

```json
{
    "name": "check_keys_pattern_inverse",
    "value": "[a-z/-]*(/{2}|/$)",
    "message": "Path must be normalized"
}
```

#### Array Validation
```json
{
    "name": "check_array_pattern",
    "value": "^[A-Z][A-Z_]*[A-Z]$", 
    "message": "Enum values must follow UPPER_SNAKE_CASE"
}
```

#### Conditional Validation
```json
{
    "name": "check_key_value",
    "value": {
        "value": "object",
        "required_sibling": "properties",
        "sibling_requirement": ".*"
    },
    "message": "Objects must have properties defined"
}
```
### ⚠️ Exception Handling

You can define exceptions for specific APIs that need to bypass certain rules:

```json
{
    "name": "check_keys_pattern",
    "value": "^[a-z_][a-z_0-9]*$",
    "message": "Properties must follow snake_case",
    "exceptions": [
        {
            "title": "Legacy API v1",
            "version": "1"
        },
        {
            "title": "Third-party Integration API",
            "version": "2"
        }
    ]
}
```

## 📝 Output Examples

### JSON Output
```json
{
    "metadata": {
        "openapi": "3.0.0",
        "info.version": "1.2.0",
        "info.title": "My API"
    },
    "errors": [
        {
            "rule_id": "B101",
            "severity": "ERROR",
            "message": "OpenAPI version must be >= 3.0.0",
            "path": "openapi"
        }
    ],
    "warnings": [
        {
            "rule_id": "B105", 
            "severity": "WARN",
            "message": "Consider adding API description",
            "path": "info.description"
        }
    ]
}
```

### YAML Output
```yaml
metadata:
  openapi: "3.0.0"
  info.version: "1.2.0"
  info.title: "My API"
errors:
  - rule_id: "B101"
    severity: "ERROR" 
    message: "OpenAPI version must be >= 3.0.0"
    path: "openapi"
warnings:
  - rule_id: "B105"
    severity: "WARN"
    message: "Consider adding API description"
    path: "info.description"
```

## 🧩 VS Code Extension

The API Linter is available as a VS Code extension that provides real-time linting with squiggly underlines and hover diagnostics directly in your specification files.

### Prerequisites

The extension requires the `linting` CLI to be available on your `PATH`. Choose one of the following installation methods:

#### Option 1: pip package (recommended for local development)

```bash
pip install --force-reinstall api-linter-101
```

> `--force-reinstall` ensures you always get the latest version, even if the same version number is already installed.

After installing, also install **yq** — it is required by the linter for YAML processing:

```bash
# macOS
brew install yq

# Linux
wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
chmod +x /usr/local/bin/yq
```

#### Option 2: Docker

If you prefer to run the linter inside Docker, ensure the Docker daemon is running and the image is available:

```bash
docker pull ghcr.io/bahag/api-linter-opensource:latest
```

> Note: The VS Code extension currently invokes the `linting` binary directly, so the pip installation is recommended for extension use.

---

### Downloading the VS Code Extension

The `.vsix` extension file is hosted in Google Cloud Storage in the `apitesting` project.

1. Open the [Google Cloud Console](https://console.cloud.google.com/) and select the **apitesting** project.
2. Navigate to **Cloud Storage → Buckets → `api-linter-opensource-vs-code-extension`**.
3. Download the latest `.vsix` file from the bucket.

Alternatively, use the `gcloud` CLI:

```bash
gcloud storage cp gs://api-linter-opensource-vs-code-extension/*.vsix .
```

---

### Installing the Extension in VS Code

1. Open VS Code.
2. Open the Command Palette: `Cmd+Shift+P` (macOS) / `Ctrl+Shift+P` (Windows/Linux).
3. Run **Extensions: Install from VSIX...**.
4. Select the downloaded `.vsix` file.
5. Reload VS Code when prompted.

---

### Using the Extension

Open any `.yaml` OpenAPI specification file. The extension activates automatically on YAML files and re-lints on every save.

#### Available Command Palette Commands

| Command | Description |
|---|---|
| `Activate Linter` | Manually trigger linting on the currently open specification file |

To run a command: open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) and type **Activate Linter**.

#### Diagnostics

- **Red squiggly lines** — `ERROR` severity issues
- **Yellow squiggly lines** — `WARN` severity issues
- **Hover** over any squiggle to see the rule ID and message (e.g. `[B111] enum property does not follow UPPER_SNAKE_CASE`)
- All findings are also listed in the **Problems panel** (`View → Problems`) with the source `api-linter`

---

## 🏗️ Development

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/BAHAG/api-linter-opensource.git
   cd api-linter-opensource
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests:**
   ```bash
   ./test_linter.sh
   ```

### Project Structure

```
api-linter-opensource/
├── local_dev/              # Development source code
│   ├── linter.py           # Main linter logic
│   ├── utils.py            # Utility functions
│   └── ...                 # Other modules
├── package/                # Package distribution
│   ├── setup.py           # Package configuration
│   ├── bin/linting        # CLI entry point
│   └── linter/            # Packaged modules
├── tests/                  # Test cases organized by rule ID
│   ├── B101/              # Tests for rule B101
│   ├── B105/              # Tests for rule B105
│   └── ...
├── rules.json             # Default rule configuration
├── sample.yaml            # Example OpenAPI specification
└── Dockerfile             # Container definition
```

### Adding New Rules

1. **Define the rule in `rules.json`:**
   ```json
   {
       "id": "B999",
       "description": "New validation rule",
       "severity": "ERROR",
       "specification-type": "OPENAPI",
       "specification-version": "ALL",
       "paths": [...]
   }
   ```

2. **Add test cases in `tests/B999/`:**
   - `passing_test.yaml` - Valid API specification
   - `failing_test.yaml` - Invalid API specification  
   - Expected output files

3. **Test your rule:**
   ```bash
   python local_dev/linter.py -s tests/B999/failing_test.yaml -r rules.json
   ```

## 🚀 Deployment & Versioning

### Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: New rules or breaking functionality changes
- **MINOR**: Updates to existing functionality 
- **PATCH**: Bug fixes and non-functional updates

### Deployment Process

1. **Update version in `package/setup.py`**
2. **Create pull request and merge**
3. **Create git tag:**
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```
4. **Docker image automatically builds and deploys to GHCR**
5. **Python package automatically deploys to PyPI**

### Available Versions

- **PyPI**: `pip install api-linter-101`
- **Docker**: `ghcr.io/bahag/api-linter-opensource:latest`
- **Docker (tagged)**: `ghcr.io/bahag/api-linter-opensource:v1.2.3`

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Contact

- **Documentation**: [Bauhaus RESTful Guidelines](https://guideline.api.bauhaus/)
- **Issues**: [GitHub Issues](https://github.com/BAHAG/api-linter-opensource/issues)
- **Contact**: shubhushan.kattel@bahag.com

## 🔗 Related Tools

- [OpenAPI Specification](https://swagger.io/specification/)
- [Spectral API Linter](https://stoplight.io/open-source/spectral)
- [yq - YAML Processor](https://github.com/mikefarah/yq)

---

<p align="center">
  <strong>Made with ❤️ by the BAHAG API Team</strong>
</p>