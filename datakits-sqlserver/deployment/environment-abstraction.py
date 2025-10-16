"""
Environment-Aware Operator Abstraction
=======================================
This solves the Docker Desktop (dev) vs Kubernetes (prod) challenge.

WHY THIS EXISTS:
- Developers use Docker Desktop (can't run K8s locally)
- Int/QA/Prod use Kubernetes
- We need the SAME business logic everywhere
- Only the execution mechanism changes
"""

import os
from typing import Dict, Any, Optional
from airflow.configuration import conf
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator


def get_environment() -> str:
    """
    Detect which environment we're running in.

    Returns: 'local', 'int', 'qa', or 'prod'
    """
    # Option 1: Environment variable
    if env := os.getenv('AIRFLOW_ENVIRONMENT'):
        return env.lower()

    # Option 2: Detect from Airflow executor
    executor = conf.get('core', 'executor')
    if executor == 'LocalExecutor':
        return 'local'
    elif executor == 'KubernetesExecutor':
        return os.getenv('ENVIRONMENT', 'int')  # Default to int

    # Option 3: Detect from hostname
    hostname = os.uname()[1]
    if 'local' in hostname or 'desktop' in hostname:
        return 'local'
    elif 'prod' in hostname:
        return 'prod'

    return 'int'  # Safe default


class DatakitOperator:
    """
    Factory that returns the appropriate operator based on environment.

    This abstraction allows the same DAG code to work everywhere.
    """

    REGISTRY_URLS = {
        'local': 'registry.localhost',
        'int': 'registry.int.company.com',
        'qa': 'registry.qa.company.com',
        'prod': 'registry.prod.company.com'
    }

    @classmethod
    def create(
        cls,
        task_id: str,
        datakit_name: str,
        datakit_version: str,
        command: Optional[str] = None,
        environment_vars: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Create appropriate operator for current environment.

        Args:
            task_id: Airflow task ID
            datakit_name: Name of datakit (e.g., 'sqlserver-bronze')
            datakit_version: Version tag (e.g., 'v1.2.3', 'latest', 'stable')
            command: Override command to run in container
            environment_vars: Environment variables to pass
            **kwargs: Additional operator arguments

        Returns:
            DockerOperator for local, KubernetesPodOperator for K8s environments
        """
        env = get_environment()
        registry = cls.REGISTRY_URLS.get(env, cls.REGISTRY_URLS['int'])
        image = f"{registry}/datakits/{datakit_name}:{datakit_version}"

        # Merge environment variables
        env_vars = {
            'ENVIRONMENT': env,
            'DATAKIT_NAME': datakit_name,
            'DATAKIT_VERSION': datakit_version,
            **(environment_vars or {})
        }

        if env == 'local':
            # Local development with Docker Desktop
            return DockerOperator(
                task_id=task_id,
                image=image,
                command=command,
                environment=env_vars,
                docker_url='unix://var/run/docker.sock',
                network_mode='bridge',
                auto_remove=True,
                mount_tmp_dir=False,  # Docker Desktop compatibility
                # Mount Kerberos ticket cache
                mounts=[
                    {
                        'source': 'krb5_cache',
                        'target': '/krb5/cache',
                        'type': 'volume',
                        'read_only': True
                    }
                ],
                **kwargs
            )
        else:
            # Kubernetes for all other environments
            return KubernetesPodOperator(
                task_id=task_id,
                name=f"{task_id}-{datakit_name}".replace('_', '-'),
                namespace=os.getenv('AIRFLOW_NAMESPACE', 'airflow'),
                image=image,
                cmds=[command] if command else None,
                env_vars=env_vars,

                # Kubernetes-specific configurations
                image_pull_policy='IfNotPresent',
                is_delete_operator_pod=True,
                hostnetwork=False,

                # Resources based on environment
                resources={
                    'local': {'requests': {'memory': '256Mi', 'cpu': '100m'}},
                    'int': {'requests': {'memory': '512Mi', 'cpu': '200m'}},
                    'qa': {'requests': {'memory': '1Gi', 'cpu': '500m'}},
                    'prod': {
                        'requests': {'memory': '2Gi', 'cpu': '1000m'},
                        'limits': {'memory': '4Gi', 'cpu': '2000m'}
                    }
                }.get(env, {'requests': {'memory': '512Mi', 'cpu': '200m'}}),

                # Mount Kerberos ticket from secret
                volumes=[
                    {
                        'name': 'kerberos-cache',
                        'secret': {
                            'secretName': 'kerberos-tickets',
                            'defaultMode': 0o400
                        }
                    }
                ],
                volume_mounts=[
                    {
                        'name': 'kerberos-cache',
                        'mountPath': '/krb5/cache',
                        'readOnly': True
                    }
                ],

                # Pull secrets for registry access
                image_pull_secrets=[f'{env}-registry-credentials'],

                **kwargs
            )


# Convenience functions for common datakits
def create_bronze_operator(task_id: str, source_table: str, version: str = 'stable', **kwargs):
    """Create Bronze ingestion operator for current environment."""
    return DatakitOperator.create(
        task_id=task_id,
        datakit_name='sqlserver-bronze',
        datakit_version=version,
        command=f'datakit-sqlserver ingest-table {source_table}',
        environment_vars={
            'SOURCE_TABLE': source_table,
            'TARGET_SCHEMA': 'bronze',
        },
        **kwargs
    )


def create_silver_operator(task_id: str, transform: str, version: str = 'stable', **kwargs):
    """Create Silver transformation operator for current environment."""
    return DatakitOperator.create(
        task_id=task_id,
        datakit_name='sqlserver-silver',
        datakit_version=version,
        command=f'datakit-transform apply {transform}',
        environment_vars={
            'TRANSFORM_NAME': transform,
            'SOURCE_SCHEMA': 'bronze',
            'TARGET_SCHEMA': 'silver',
        },
        **kwargs
    )