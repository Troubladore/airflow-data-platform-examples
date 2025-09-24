# Why This Architecture? The Story Behind Our Design

## 🎯 The Problem We're Solving

Our data engineers need to ingest data from SQL Server databases that require Windows Authentication (Kerberos/NT Auth). But we have several constraints that make this challenging:

1. **Self-hosted Astronomer** - No cloud magic, we manage everything
2. **Delinea for secrets** - Corporate requirement, can't store secrets elsewhere
3. **Multiple warehouses** - Same source data goes to different destinations
4. **Docker locally, Kubernetes in production** - Different execution environments

## 📖 How We Got Here: The Journey

### Chapter 1: "Just Use Astronomer Cloud" ❌

**Initial thought**: Astronomer Cloud handles everything!

**Reality**: We're self-hosting due to data sovereignty requirements. We need to build what Astronomer Cloud provides:
- Our own registry
- Our own deployment pipeline
- Our own secrets management

### Chapter 2: "Just Store Credentials in Airflow" ❌

**Initial thought**: Use Airflow's Connections UI!

**Reality**: Corporate security mandates Delinea as the sole secrets store. We needed a pattern that:
- Gets credentials from Delinea
- Never persists them in Airflow
- Rotates automatically

**Solution**: Kerberos sidecar that manages tickets independently.

### Chapter 3: "Just Copy the DAG for Each Warehouse" ❌

**Initial thought**: Simple copy-paste for each destination!

**Reality**: When source schema changed, we had to update 10 different DAGs. Maintenance nightmare.

**Solution**: Datakits - define extraction once, reuse everywhere:
```
One Datakit (v1.2.3) → Used by all warehouses
Schema changes → Update one place → Everyone gets it
```

### Chapter 4: "Just Use KubernetesExecutor Everywhere" ❌

**Initial thought**: Kubernetes is our standard!

**Reality**: Developers have Docker Desktop, not Kubernetes. They can't test locally.

**Solution**: Environment abstraction layer that uses:
- DockerOperator locally
- KubernetesPodOperator in K8s
- Same business logic everywhere

## 🏗️ Why Three Layers?

### Layer 1: Platform (Main Repository)
**Purpose**: Foundational capabilities everyone needs

- **Kerberos sidecar**: Because Delinea + NT Auth
- **Astronomer base**: Because self-hosted
- **Registry push**: Because no cloud service

### Layer 2: Datakits (Examples Repository)
**Purpose**: Reusable business logic

- **Source datakits**: Define extraction once
- **Bronze datakits**: Standardize ingestion
- **Version independently**: Update without touching platform

### Layer 3: Warehouse (Examples Repository)
**Purpose**: Destination-specific configuration

- **Multiple targets**: Finance, Marketing, Analytics warehouses
- **Independent schemas**: Each can evolve separately
- **Pulls from registry**: Consumption model, not build

## 🔄 Why the Registry Flow?

```
Without Registry (BAD):
- Every team builds their own images
- No versioning control
- Can't track what's deployed where

With Registry (GOOD):
registry.localhost/datakits/sqlserver-bronze:v1.2.3
                   ↓
    Consumed by all environments consistently
```

## 🎭 Why Different Operators for Different Environments?

**The Problem**:
- Developers: "I have Docker Desktop"
- DevOps: "Production is Kubernetes"
- Data Engineers: "I just want my DAG to work"

**The Solution**:
```python
# Same DAG code
ingest = DatakitOperator.create(...)

# Becomes DockerOperator locally
# Becomes KubernetesPodOperator in prod
# Data engineer doesn't care
```

## 🔐 Why Kerberos Sidecar?

**Traditional Approach**: Put username/password in connection
**Why That Fails**:
1. Delinea won't allow it
2. NT Auth needs Kerberos tickets, not passwords
3. Tickets expire and need renewal

**Our Approach**:
```
Delinea → Keytab → Sidecar → Ticket → Shared Volume → All Containers
         Secure    Managed   Auto-     Never         Access
                             Renewed   Persisted
```

## 💡 Why Datakits Instead of Just Operators?

**Operators Alone**:
- Logic scattered across DAGs
- Version conflicts
- Testing nightmare
- No isolation

**Datakits**:
- Self-contained units
- Version controlled
- Tested independently
- Resource isolation
- Deploy once, use many

## 📊 The Payoff: What This Architecture Enables

1. **Developer Productivity**
   - Works on laptop identically to production
   - No "works on my machine" problems

2. **Operational Excellence**
   - Version everything
   - Deploy through GitOps
   - Rollback capabilities

3. **Security Compliance**
   - Delinea integration ✓
   - No embedded credentials ✓
   - Audit trail ✓

4. **Business Agility**
   - New warehouse? Reuse datakits
   - Schema change? Update one place
   - New source? Follow the pattern

## 🚀 Alternative Approaches We Considered

### "Use Meltano/Singer Taps"
- ❌ Doesn't support Kerberos
- ❌ Not Airflow-native
- ❌ Another tool to manage

### "Use Fivetran/Airbyte"
- ❌ Can't self-host with our requirements
- ❌ Doesn't integrate with Delinea
- ❌ Licensing costs

### "Build Custom Python Scripts"
- ❌ No reusability
- ❌ No versioning
- ❌ No isolation

## 📝 In Summary

This architecture exists because:

1. **Self-hosted Astronomer** requires us to build cloud-like capabilities
2. **Delinea requirement** necessitates the Kerberos sidecar pattern
3. **Multiple warehouses** justify the datakit abstraction
4. **Docker/K8s split** demands environment abstraction
5. **Enterprise scale** needs versioning and GitOps

It's not over-engineered - it's exactly what's needed for our constraints. Each layer and component addresses a specific requirement that simpler approaches couldn't handle.

---

*"Make it as simple as possible, but not simpler." - This architecture is as simple as our requirements allow.*