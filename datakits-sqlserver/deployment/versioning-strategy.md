# Versioning Strategy

How we version and release components across the three-layer architecture.

## 📦 Version Format

All components follow Semantic Versioning: `vMAJOR.MINOR.PATCH`

```
v1.2.3
│ │ └── Patch: Bug fixes, no API changes
│ └──── Minor: New features, backward compatible
└────── Major: Breaking changes
```

## 🏗️ Layer-Specific Versioning

### Layer 1: Platform Components

**Repository**: `airflow-data-platform`
**Registry Path**: `registry.localhost/platform/`

```yaml
# Platform components version together
kerberos-sidecar:v1.0.0
astronomer-kerberos:v1.0.0

# Tagged in Git as
git tag platform-v1.0.0
```

**Release Triggers**:
- PATCH: Security updates, bug fixes
- MINOR: New Astronomer version, added libraries
- MAJOR: Breaking changes to base image

### Layer 2: Datakits

**Repository**: `airflow-data-platform-examples`
**Registry Path**: `registry.localhost/datakits/`

```yaml
# Each datakit versions independently
sqlserver-source:v2.1.0
sqlserver-bronze:v1.3.2

# Tagged in Git as
git tag datakit-sqlserver-source-v2.1.0
git tag datakit-sqlserver-bronze-v1.3.2
```

**Release Triggers**:
- PATCH: Bug fixes, performance improvements
- MINOR: New tables, additional transformations
- MAJOR: Schema changes, API modifications

### Layer 3: Warehouse Configurations

**Repository**: `airflow-data-platform-examples`
**No Registry**: Configurations, not images

```yaml
# Version via Git tags
git tag warehouse-bronze-v1.0.0
```

## 🔄 Environment Promotion Strategy

### Version Channels

```
latest → development → stable → production
```

| Channel | Purpose | Environment | Auto-Update |
|---------|---------|-------------|-------------|
| `latest` | Active development | Local only | Yes |
| `development` | Integration testing | INT | Yes |
| `stable` | Pre-production | QA | No |
| `production` | Production verified | PROD | No |

### Promotion Flow

```
Developer commits
       ↓
CI builds → :latest
       ↓
Tests pass → :v1.2.3 + :development
       ↓
QA approves → :stable
       ↓
Prod deploy → :production
```

## 🎯 Dependency Management

### Platform → Datakit Dependencies

```dockerfile
# Datakit Dockerfile
ARG PLATFORM_VERSION=v1.0.0
FROM registry.localhost/platform/astronomer-kerberos:${PLATFORM_VERSION}
```

**Compatibility Matrix**:

| Datakit Version | Requires Platform | Notes |
|-----------------|-------------------|-------|
| v1.0.x | v1.0.x | Initial release |
| v1.1.x | v1.0.x | Backward compatible |
| v2.0.x | v2.0.x | Breaking changes |

### DAG → Datakit Dependencies

```python
# In DAG
DATAKIT_VERSIONS = {
    'local': 'latest',
    'int': 'development',
    'qa': 'stable',
    'prod': 'v1.2.2'  # Explicit version
}
```

## 📋 Release Process

### 1. Platform Release (Quarterly)

```bash
# In airflow-data-platform repo
git checkout main
git pull

# Update versions
vim VERSION  # Update to 1.1.0

# Build and test
make test

# Tag and push
git tag platform-v1.1.0
git push --tags

# CI/CD builds and pushes to registry
# registry.localhost/platform/kerberos-sidecar:v1.1.0
# registry.localhost/platform/astronomer-kerberos:v1.1.0
```

### 2. Datakit Release (Weekly/As Needed)

```bash
# In airflow-data-platform-examples repo
cd datakits-sqlserver

# Update version in pyproject.toml
vim datakit_sqlserver_bronze_kerberos/pyproject.toml

# Build and test locally
make test

# Tag specific datakit
git tag datakit-sqlserver-bronze-v1.3.2
git push --tags

# CI/CD builds and pushes
# registry.localhost/datakits/sqlserver-bronze:v1.3.2
```

### 3. Promotion to Environments

```yaml
# ArgoCD/Flux GitOps repository
# environments/int/kustomization.yaml
images:
  - name: registry.localhost/datakits/sqlserver-bronze
    newTag: v1.3.2  # ← Update this

# Commit triggers deployment
git commit -m "chore: promote sqlserver-bronze to v1.3.2 in INT"
git push
```

## 🔍 Version Discovery

### Check What's Deployed

```bash
# Local environment
docker ps --format "table {{.Image}}\t{{.Status}}"

# Kubernetes environment
kubectl get pods -o jsonpath="{..image}" | tr -s '[[:space:]]' '\n' | sort -u

# Registry catalog
curl http://registry.localhost/v2/_catalog
curl http://registry.localhost/v2/datakits/sqlserver-bronze/tags/list
```

### Version in Logs

Every datakit logs its version on startup:

```
[2025-01-15 10:00:00] Starting datakit-sqlserver-bronze v1.3.2
[2025-01-15 10:00:00] Platform version: v1.1.0
[2025-01-15 10:00:00] Environment: production
```

## 📊 Version Lifecycle

### Support Matrix

| Version | Status | Support Until | Notes |
|---------|--------|---------------|-------|
| v1.0.x | EOL | 2024-12-31 | Migrate to v1.1+ |
| v1.1.x | Security Only | 2025-06-30 | Bug fixes only |
| v1.2.x | Active | 2025-12-31 | Current stable |
| v2.0.x | Development | - | Next major |

### Breaking Change Policy

1. **Deprecation Notice**: 2 releases before removal
2. **Migration Guide**: Provided with deprecation
3. **Compatibility Mode**: 1 release overlap
4. **Forced Update**: Only for security issues

## 🚀 Rollback Strategy

### Quick Rollback

```bash
# Update image tag in GitOps repo
git revert HEAD
git push

# Or manually in emergency
kubectl set image deployment/bronze-processor \
  bronze-processor=registry.localhost/datakits/sqlserver-bronze:v1.3.1
```

### Version Pinning

```python
# For stability, production DAGs pin exact versions
DATAKIT_VERSIONS = {
    'prod': 'v1.2.2',  # Not 'stable' or 'latest'
}
```

## 📝 Release Notes Template

```markdown
# Release: datakit-sqlserver-bronze v1.3.2

## What's New
- Added support for temporal tables
- Performance improvements for large batches

## Bug Fixes
- Fixed Unicode handling in column names
- Resolved memory leak in connection pooling

## Breaking Changes
- None

## Dependencies
- Requires platform v1.1.0 or higher
- Compatible with warehouse v2.x

## Migration Notes
- No action required for existing deployments

## Docker Images
- registry.localhost/datakits/sqlserver-bronze:v1.3.2
- registry.localhost/datakits/sqlserver-bronze:stable (updated)
```

## 🎯 Version Standards

1. **Always tag releases** - No unversioned deployments
2. **Never use `latest` in production** - Explicit versions only
3. **Document dependencies** - Platform and warehouse compatibility
4. **Test version upgrades** - Automated compatibility tests
5. **Monitor version drift** - Alert if environments diverge

---

This versioning strategy ensures predictable deployments, easy rollbacks, and clear dependency management across our three-layer architecture.