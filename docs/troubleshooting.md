# Troubleshooting Guide

Common issues when working with Airflow Data Platform Examples and their solutions.

## 🚨 HTTPS Certificate Warnings

### Problem: "Your connection is not private" browser warnings

**Symptoms:**
- Browser shows certificate warnings for `https://airflow.localhost`
- curl commands fail without `-k` flag
- Platform services require `--insecure` flags to access

**Root Cause:**
The platform setup was incomplete - certificates exist but the Certificate Authority (CA) is not trusted by your system.

**Solution:**
Re-run the complete platform setup process:

```bash
# Navigate to platform repository
cd /path/to/airflow-data-platform

# Run the complete setup (this installs mkcert and trusts the CA)
ansible-playbook -i ansible/inventory/local-dev.ini ansible/site.yml --ask-become-pass

# Validate certificate trust
ansible-playbook -i ansible/inventory/local-dev.ini ansible/validate-all.yml
```

**Expected Result:**
- ✅ Browser loads `https://airflow.localhost` without warnings
- ✅ curl works without `-k` flag: `curl https://traefik.localhost`
- ✅ All platform services have trusted HTTPS

### Problem: Demo scripts use wrong Docker Compose configuration

**Symptoms:**
- Registry logs show: "open /certs/cert.pem: no such file or directory"
- HTTPS services work with `-k` but show certificate errors
- Traefik can't find certificates

**Root Cause:**
Using static `prerequisites/traefik-registry/docker-compose.yml` instead of Ansible-generated platform services.

**Solution:**
1. Stop incorrect services:
   ```bash
   docker compose -f /path/to/airflow-data-platform/prerequisites/traefik-registry/docker-compose.yml down
   ```

2. Use proper platform services:
   ```bash
   cd ~/platform-services/traefik && docker compose up -d
   ```

**Prevention:**
Always use Ansible-generated services (`~/platform-services/traefik/`) which properly mount WSL2 certificates from `~/.local/share/certs/`. The static prerequisite files are templates only.

## 🔧 Platform Setup Issues

### Problem: Examples can't connect to platform services

**Symptoms:**
- `uv sync` succeeds but platform integration fails
- Connection refused errors to localhost services
- Docker network issues between examples and platform

**Solution:**
1. Verify platform is running:
   ```bash
   curl -k https://traefik.localhost/api/http/services
   ```

2. Check Docker networks:
   ```bash
   docker network ls | grep -E "(edge|data-processing)"
   ```

3. Restart platform if needed:
   ```bash
   cd ~/platform-services/traefik && docker compose restart
   ```

### Problem: Permission errors during platform setup

**Symptoms:**
- Ansible playbook fails with permission denied
- Cannot install certificates or mkcert
- Docker commands fail

**Solution:**
Ensure your user has proper permissions:

```bash
# Check if passwordless sudo is configured
sudo -n true && echo "✅ Passwordless sudo OK" || echo "❌ Password required"

# If password required, you can configure passwordless sudo:
sudo visudo
# Add line: your_username ALL=(ALL) NOPASSWD:ALL
```

## 📊 Data Processing Issues

### Problem: Transformation functions not found

**Symptoms:**
- `ImportError: No module named 'datakits'`
- DAG import errors in Airflow
- Platform framework not accessible

**Solution:**
Verify the platform dependency is properly installed:

```bash
cd pagila-implementations/pagila-sqlmodel-basic
uv sync --reload  # Reinstall dependencies
python -c "import sqlmodel_framework; print('✅ Framework available')"
```

### Problem: Database connection failures

**Symptoms:**
- Cannot connect to PostgreSQL databases
- "Connection refused" errors
- Port binding conflicts

**Solution:**
1. Check database containers:
   ```bash
   docker ps --filter name=postgres
   ```

2. Verify port availability:
   ```bash
   netstat -tulpn | grep :5432
   ```

3. Restart data infrastructure:
   ```bash
   ./scripts/shutdown-demo.sh
   ./scripts/demo-everything-working.sh
   ```

## 🎯 Getting Help

If these solutions don't resolve your issue:

1. **Check validation output:**
   ```bash
   cd /path/to/airflow-data-platform
   ansible-playbook -i ansible/inventory/local-dev.ini ansible/validate-all.yml
   ```

2. **Review container logs:**
   ```bash
   docker compose -f ~/platform-services/traefik/docker-compose.yml logs -f
   ```

3. **Test manual connectivity:**
   ```bash
   curl -k https://traefik.localhost/api/http/services
   curl -k https://registry.localhost/v2/_catalog
   ```

4. **Platform repository issues:** [Create issue](https://github.com/Troubladore/airflow-data-platform/issues)
5. **Examples repository issues:** [Create issue](https://github.com/Troubladore/airflow-data-platform-examples/issues)

---

## 📚 Related Documentation

- [Platform Setup Guide](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/getting-started.md)
- [Platform Troubleshooting](https://github.com/Troubladore/airflow-data-platform/blob/main/docs/getting-started.md#troubleshooting)
- [Examples Getting Started](./getting-started.md)