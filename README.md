# envault

A local secrets manager that encrypts and organizes `.env` files across projects with per-directory access control.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install envault
```

---

## Usage

Initialize envault in your project directory:

```bash
envault init
```

Store a secret:

```bash
envault set DATABASE_URL "postgres://user:pass@localhost/mydb"
```

Retrieve and inject secrets into your environment:

```bash
envault run -- python app.py
```

Export secrets to a `.env` file:

```bash
envault export > .env
```

Access is scoped per directory — secrets stored in `~/projects/api` are not accessible from `~/projects/frontend`.

---

## How It Works

- Secrets are encrypted using AES-256 and stored in `~/.envault/`.
- Each project directory gets its own isolated vault, keyed by path.
- A master password (or key file) is required to unlock any vault.

---

## Requirements

- Python 3.8+
- `cryptography` >= 41.0

---

## License

MIT © 2024 — see [LICENSE](LICENSE) for details.