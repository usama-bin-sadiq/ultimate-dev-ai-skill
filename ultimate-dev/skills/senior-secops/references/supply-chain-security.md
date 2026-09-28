<!-- Moved verbatim from senior-secops/SKILL.md, the 'Supply Chain Security' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Supply Chain Security

Protect against dependency and artifact tampering with SBOM generation, artifact signing, and SLSA compliance.

**SBOM Generation:**
- **syft** — generates SBOMs from container images or source dirs (SPDX, CycloneDX formats)
- **cyclonedx-cli** — CycloneDX-native tooling; merge multiple SBOMs for mono-repos

```bash
# Generate SBOM from container image
syft packages ghcr.io/org/app:latest -o cyclonedx-json > sbom.json
```

**Artifact Signing (Sigstore/cosign):**
```bash
# Sign a container image (keyless via OIDC)
cosign sign ghcr.io/org/app:latest
# Verify signature
cosign verify ghcr.io/org/app:latest --certificate-identity=ci@org.com --certificate-oidc-issuer=https://token.actions.githubusercontent.com
```

**SLSA Levels Overview:**
| Level | Requirement | What It Proves |
|-------|-------------|----------------|
| 1 | Build process documented | Provenance exists |
| 2 | Hosted build service, signed provenance | Tamper-resistant provenance |
| 3 | Hardened build platform, non-falsifiable provenance | Tamper-proof build |
| 4 | Two-party review, hermetic builds | Maximum supply-chain assurance |

> **Cross-references:** `security-pen-testing` (vulnerability exploitation testing), `dependency-auditor` (license and CVE audit for dependencies).

---
