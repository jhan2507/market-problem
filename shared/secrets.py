"""
Secrets management wrapper.
Supports environment variables, Vault, and AWS Secrets Manager.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SecretsManager:
    """Secrets management with multiple backends."""
    
    def __init__(self, backend: str = "env"):
        """
        Initialize secrets manager.
        
        Args:
            backend: Backend type - "env", "vault", or "aws"
        """
        self.backend = backend
        self._vault_client = None
        self._aws_client = None
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret value.
        
        Args:
            key: Secret key
            default: Default value if not found
        
        Returns:
            Secret value or default
        """
        if self.backend == "env":
            return os.getenv(key, default)
        elif self.backend == "vault":
            return self._get_vault_secret(key, default)
        elif self.backend == "aws":
            return self._get_aws_secret(key, default)
        else:
            logger.warning(f"Unknown backend: {self.backend}, falling back to env")
            return os.getenv(key, default)
    
    def _get_vault_secret(self, key: str, default: Optional[str]) -> Optional[str]:
        """Get secret from Vault."""
        try:
            if self._vault_client is None:
                import hvac
                vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
                vault_token = os.getenv("VAULT_TOKEN")
                self._vault_client = hvac.Client(url=vault_addr, token=vault_token)
            
            # Parse key as path:secret_key
            if ":" in key:
                path, secret_key = key.split(":", 1)
                secret = self._vault_client.secrets.kv.v2.read_secret_version(path=path)
                return secret.get("data", {}).get("data", {}).get(secret_key, default)
            else:
                # Use key as path, return all data
                secret = self._vault_client.secrets.kv.v2.read_secret_version(path=key)
                return str(secret.get("data", {}).get("data", {}))
        except ImportError:
            logger.warning("hvac not installed, cannot use Vault backend")
            return os.getenv(key, default)
        except Exception as e:
            logger.error(f"Error getting secret from Vault: {e}")
            return default
    
    def _get_aws_secret(self, key: str, default: Optional[str]) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        try:
            if self._aws_client is None:
                import boto3
                self._aws_client = boto3.client('secretsmanager')
            
            response = self._aws_client.get_secret_value(SecretId=key)
            return response.get('SecretString', default)
        except ImportError:
            logger.warning("boto3 not installed, cannot use AWS backend")
            return os.getenv(key, default)
        except Exception as e:
            logger.error(f"Error getting secret from AWS: {e}")
            return default
    
    def set_secret(self, key: str, value: str):
        """
        Set secret value (only for env backend).
        
        Args:
            key: Secret key
            value: Secret value
        """
        if self.backend == "env":
            os.environ[key] = value
        else:
            logger.warning(f"set_secret not supported for backend: {self.backend}")


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager(backend: str = None) -> SecretsManager:
    """Get global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        backend = backend or os.getenv("SECRETS_BACKEND", "env")
        _secrets_manager = SecretsManager(backend)
    return _secrets_manager


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get secret value using global secrets manager."""
    return get_secrets_manager().get_secret(key, default)

