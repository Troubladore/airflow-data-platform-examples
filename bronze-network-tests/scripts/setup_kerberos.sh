#!/bin/bash
#
# Setup Kerberos ticket for container testing
#
# This script ensures we have a valid Kerberos ticket before running tests

set -e

echo "=========================================="
echo "Kerberos Setup for Bronze Network Tests"
echo "=========================================="

# Check if we're in WSL2 or Linux
if grep -qi microsoft /proc/version; then
    echo "✓ Running in WSL2"
else
    echo "✓ Running in Linux"
fi

# Check for Kerberos configuration
if [ -f /etc/krb5.conf ]; then
    echo "✓ Kerberos config found at /etc/krb5.conf"
else
    echo "✗ No Kerberos config found!"
    echo "Please ensure /etc/krb5.conf is configured for ERUDITIS.LAB"
    exit 1
fi

# Check for existing ticket
echo ""
echo "Checking for existing Kerberos ticket..."
if klist 2>/dev/null | grep -q "emaynard@ERUDITIS.LAB"; then
    echo "✓ Valid ticket found for emaynard@ERUDITIS.LAB"
    klist | grep "Valid starting\|Expires"
else
    echo "No valid ticket found. Getting new ticket..."
    echo ""
    echo "Please enter password for emaynard@ERUDITIS.LAB"
    echo "(Password: Quicksand123!)"
    kinit emaynard@ERUDITIS.LAB

    if [ $? -eq 0 ]; then
        echo "✓ Successfully obtained Kerberos ticket"
        klist | grep "Valid starting\|Expires"
    else
        echo "✗ Failed to obtain Kerberos ticket"
        exit 1
    fi
fi

# Check credential cache location
echo ""
echo "Credential cache location:"
if [ -n "$KRB5CCNAME" ]; then
    echo "  KRB5CCNAME=$KRB5CCNAME"
else
    echo "  Using default (typically /tmp/krb5cc_$(id -u))"
fi

# Verify we can resolve ERUDITIS.LAB hosts
echo ""
echo "Verifying DNS resolution..."
for host in dc1.eruditis.lab sqlpg.eruditis.lab; do
    if getent hosts $host >/dev/null 2>&1; then
        ip=$(getent hosts $host | awk '{print $1}')
        echo "  ✓ $host resolves to $ip"
    else
        echo "  ✗ Cannot resolve $host"
        echo "    Add to /etc/hosts: 10.50.50.11 dc1.eruditis.lab"
        echo "    Add to /etc/hosts: 10.50.50.13 sqlpg.eruditis.lab"
    fi
done

# Test connectivity to Postgres
echo ""
echo "Testing network connectivity to sqlpg.eruditis.lab..."
if nc -zv sqlpg.eruditis.lab 5432 2>&1 | grep -q succeeded; then
    echo "  ✓ Port 5432 is reachable"
else
    echo "  ✗ Cannot reach sqlpg.eruditis.lab:5432"
    echo "    Check network connectivity and firewall rules"
fi

echo ""
echo "=========================================="
echo "Setup complete! Ready to run tests."
echo "=========================================="
echo ""
echo "To run Kerberos tests:"
echo "  docker-compose run test-kerberos"
echo ""
echo "To run all tests:"
echo "  docker-compose up --build"