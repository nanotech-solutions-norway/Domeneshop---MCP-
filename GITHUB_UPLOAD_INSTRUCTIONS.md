# GitHub Upload Instructions — 22:34, 25.06.2026

Target repository:

```text
nanotech-solutions-norway/Domeneshop---MCP-
```

The repository is currently private and empty. If GitHub web upload is used, upload the folder contents exactly as structured.

## Git command route

```bash
git clone https://github.com/nanotech-solutions-norway/Domeneshop---MCP-.git
cd Domeneshop---MCP-

# Copy all package contents into this folder, then:
git add .
git commit -m "Initialize Domeneshop MCP phase plan"
git push origin main
```

## Validation route

After upload:

```bash
python scripts/validate_repository_structure.py
```

Expected result:

```text
Repository structure validation passed.
```

## Important

Do not commit real `.env` files, API tokens, API secrets, SFTP passwords, or SSH keys.
