# Lazzy Commit 😪💤

AI-powered commit message generator for git with built-in security validation and conventional commit format enforcement.

## ✨ Features

- 🤖 **AI-Generated Messages**: Uses Google Gemini to analyze git diffs and generate meaningful commit messages
- 🔒 **Security Validation**: Automatically detects API keys, tokens, and sensitive data in commits
- 📝 **Conventional Commits**: Enforces conventional commit format (feat, fix, docs, etc.)
- ✅ **Smart Validation**: Validates message length, content quality, and format
- ✏️ **Interactive Editing**: Review, edit, or regenerate commit messages before committing
- 🚀 **Auto-Push**: Optional flag to push changes immediately after commit

## 📋 Requirements

- Python 3.7+
- Git
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

## 🚀 Quick Start

### Windows

1. **Clone and setup**:
   ```powershell
   git clone <repository-url>
   cd lazzy-commit
   .\setup-path.bat
   ```

2. **Add to PATH**:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";<repository path>", "User")
   ```
   example:
   ```powershell
   $ [Environment]::SetEnvironmentVariable("Path", $env:Path + ";D:\Repositories\lazzy-commit", "User")
   ```
   ⚠️ You must restart your pc after adding to PATH for changes to take effect.

3. **Configure API Key**:
   - Edit `.env` file
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

4. **Run from any git repository**:
   ```powershell
   lazzycommit
   ```

## 📖 Usage

### Basic Usage

Stage your changes and run:
```bash
lazzycommit
```

The tool will:
1. 🔍 Analyze your staged changes
2. 🤖 Generate a commit message using AI
3. 📝 Display the message for review
4. ✅ Prompt you to confirm, edit, or cancel

### Auto-Push

Commit and push in one command:
```bash
lazzycommit --push
# or
lazzycommit -p
```

### Interactive Prompts

After message generation, you can:
- `y` (yes) - Accept and commit
- `n` (no) - Cancel
- `e` (edit) - Edit the message before committing

## ⚙️ Configuration

Edit `.env` to customize behavior:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Validation Settings
MAX_SUBJECT_LENGTH=100

# Security Checks
CHECK_API_KEYS=true
CHECK_SENSITIVE_DATA=true

# Format Enforcement
ENFORCE_CONVENTIONAL_COMMITS=true
ENFORCE_LENGTH_LIMIT=true
```

### Validation Rules

**Security Validators**:
- ✋ Blocks commits containing API keys, tokens, passwords
- ✋ Detects sensitive patterns (AWS keys, private keys, etc.)

**Format Validators**:
- ✅ Enforces conventional commit format: `type: description`
- ✅ Supported types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `build`, `ci`, `modify`, `revert`
- ✅ Subject line length limit (default: 100 characters)

**Content Validators**:
- ✋ Blocks WIP/TODO/FIXME commits
- ✅ Ensures minimum message length (10 characters)

## 🔧 Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Locally

```bash
python main.py
```

## 📄 License

MIT License - Feel free to use and modify

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

---

**Made with ❤️ and a bit of laziness** 😪💤
