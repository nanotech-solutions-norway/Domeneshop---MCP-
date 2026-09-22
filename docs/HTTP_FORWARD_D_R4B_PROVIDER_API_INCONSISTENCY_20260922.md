# D-R4B HTTP-forward provider API inconsistency — support evidence

Date: 2026-09-22
Repository: nanotech-solutions-norway/Domeneshop---MCP-
Environment: isolated non-production
Domain: atlas-mcp-sandbox.no
Forward host: mcp-forward-validation

## Executive summary

The isolated HTTP-forward CREATE operation is accepted and independently verified through the list-forwards endpoint.

A separately authorized exact UPDATE was attempted against the documented host-addressed PUT endpoint. The provider returned HTTP 404 `not_found`. A subsequent GET-only recovery verifier proved that the forward remained exactly in the previously accepted CREATE state; therefore the failed UPDATE produced no effective provider-state change.

A dedicated GET-only route diagnostic then confirmed that the same forward is visible through the list endpoint while every tested single-forward host-addressed GET route returns HTTP 404.

No further UPDATE or DELETE attempt is authorized or planned until Domeneshop clarifies the provider behavior.

## Accepted provider state

Target SHA256:

`23cc343ce4a03fb910e58a371604ff85a7c49c16c062e15ba8238ec662fea831`

Accepted CREATE-state payload SHA256:

`2fbfc99c2747d313ecdd0477aab0c9c67f8f9e66c19c7fa90920bb20ce57a926`

Accepted state:

```json
{
  "host": "mcp-forward-validation",
  "frame": false,
  "url": "https://atlas-mcp-sandbox.no/"
}
```

## UPDATE attempt

Authorized release:

`D-R4B-HTTP-FORWARD-UPDATE-20260826-001`

Required-before payload SHA256:

`2fbfc99c2747d313ecdd0477aab0c9c67f8f9e66c19c7fa90920bb20ce57a926`

Candidate UPDATE payload SHA256:

`961fea82b0837c992c66f11aaacadf9642782b0cd263ce374d4d07b4d18c8ebb`

Candidate URL:

`https://atlas-mcp-sandbox.no/?mcp-forward-validation=updated`

Observed provider result:

```text
error_class=not_found
provider_mutation_attempted=true
provider_mutation_performed=unknown
```

No automatic delete or rollback was performed.

## Recovery verification

GET-only recovery run:

- workflow run: `35509703761`
- job: `106075355241`
- status: success
- verification method: `list_forwards`
- attempts used: `1`
- result: `exact_create_state_verified`

This establishes that the failed PUT did not produce an effective provider-state change.

## Single-forward route diagnostic

GET-only route diagnostic run:

- workflow run: `35538245224`
- job: `106151060928`
- status: success
- provider mutation performed: false
- accepted CREATE state verified by list endpoint: true

Observed host-addressed GET results:

| Probe | Result |
| --- | --- |
| documented host path | HTTP 404 |
| documented host path + trailing slash | HTTP 404 |
| FQDN host path | HTTP 404 |
| FQDN host path + trailing slash | HTTP 404 |

The list endpoint in the same diagnostic returned the exact expected forward.

## Documented Domeneshop contract

Current Domeneshop API documentation defines:

- list: `GET /v0/domains/{domainId}/forwards/`
- find by host: `GET /v0/domains/{domainId}/forwards/{host}`
- update by host: `PUT /v0/domains/{domainId}/forwards/{host}`
- delete by host: `DELETE /v0/domains/{domainId}/forwards/{host}`

For update, the documentation states that the request-body `host` must not change.

Documentation:
https://api.domeneshop.no/docs/

## Official Domeneshop Python client

Domeneshop's official `python-domeneshop` client implements the same routing model:

- `get_forward(domain_id, host)` -> `/domains/{domain_id}/forwards/{host}`
- `modify_forward(domain_id, host, ...)` -> `PUT /domains/{domain_id}/forwards/{host}`
- `delete_forward(domain_id, host)` -> `DELETE /domains/{domain_id}/forwards/{host}`

Repository:
https://github.com/domeneshop/python-domeneshop

No matching open or closed public issue describing this 404 behavior was found in that repository as of 2026-09-22.

## Safety conclusion

The MCP implementation must not retry the UPDATE while the provider lookup semantics are unresolved.

Current enforced state remains:

```text
HTTP_FORWARD_CREATE_AUTHORIZED=false
HTTP_FORWARD_UPDATE_AUTHORIZED=false
HTTP_FORWARD_DELETE_AUTHORIZED=false
BROADER_OVERWRITE_AUTHORIZED=false
WRITE_TOOLS_ENABLED=false
DRY_RUN_DEFAULT=true
```

The accepted provider state remains the exact original CREATE state.

## Questions for Domeneshop support

1. Why does `GET /v0/domains/{domainId}/forwards/` return the forward with host `mcp-forward-validation` while `GET /v0/domains/{domainId}/forwards/mcp-forward-validation` returns HTTP 404?
2. Is the documented host-addressed GET/PUT/DELETE endpoint currently supported for hosts containing hyphens?
3. Is a different identifier, normalization rule, URL encoding, or path format required for single-forward lookup/update?
4. Is this a known API defect or an account/domain-specific issue?
5. What exact request path should be used to update this existing forward without deleting and recreating it?
6. Can Domeneshop confirm whether an HTTP 404 from the PUT endpoint guarantees no mutation occurred before the response?
