# Atlas, SolarEX, and Domeneshop Integration Notes

## Purpose

These notes explain how the Domeneshop MCP bridge relates to the current Atlas and SolarEX service estate.

## Atlas estate

```text
monitor.atlas-ai.no -> Atlas Monitor -> /www/atlas_control
pip.atlas-ai.no -> Atlas PIP -> /www/atlas_pip2
```

## SolarEX estate

```text
forms.nanotech-solutions.com/solarex_forms -> SolarEX Forms API -> /www/solarex_forms
forms.nanotech-solutions.com/solarex_admin -> SolarEX Admin -> /www/solarex_forms
```

## Domeneshop role

Domeneshop-related hosting is used as the PHP and hosted-file layer for selected service endpoints.

The MCP bridge currently supports:

```text
Domeneshop API read inspection
hosted-file read inspection
HTTP diagnostics
planning reports
recovery planning
control-plane preflight
runtime readiness
operations validation
estate validation
```

## Scope boundary

The bridge does not currently perform live DNS changes, hosted-file transfer execution, recovery execution, or shell execution.

## Operator review questions

1. Is the service still active?
2. Is the mapped domain correct?
3. Is the mapped remote root correct?
4. Is the check target correct?
5. Is the service owner correct?
6. Is the service covered by an allowed root?

## Future expansion note

Future service additions should be added first to `config/estate-targets.example.json`, then validated by `scripts/estate_validate.py` before any deployment planning is attempted.
