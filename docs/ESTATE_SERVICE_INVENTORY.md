# Estate Service Inventory

## Purpose

This document maps the current Atlas, SolarEX, and Domeneshop service estate used by the MCP bridge.

## Registry file

```text
config/estate-targets.example.json
```

## Service targets

| Service | Domain | Check path | Remote root | Owner |
|---|---|---|---|---|
| SolarEX Forms API | forms.nanotech-solutions.com | /solarex_forms/health.php | /www/solarex_forms | SolarEX |
| SolarEX Admin | forms.nanotech-solutions.com | /solarex_admin/ | /www/solarex_forms | SolarEX |
| Atlas Monitor | monitor.atlas-ai.no | /login.php | /www/atlas_control | Atlas |
| Atlas PIP | pip.atlas-ai.no | /health.php | /www/atlas_pip2 | Atlas |

## Allowed remote roots

```text
/www
/www/solarex_forms
/www/atlas_control
/www/atlas_pip2
```

## Validation command

```bash
python scripts/estate_validate.py --registry config/estate-targets.example.json --output phase11-estate-validation-report.json
```

## Use in operations

The estate registry is used for:

```text
service inventory
endpoint review
remote root review
operator scope review
future deployment scoping
```

## Safety position

The estate registry is declarative. It does not enable live change operations.
