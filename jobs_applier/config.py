# jobs_applier/config.py

import os
import yaml
from typing import Any, Dict, Optional

DEFAULT_CONFIG_PATH = "config.yaml"

ENV_VAR_MAP = {
    # Maps environment variable -> (location in config, key in that dict)
    "LINKEDIN_EMAIL": ("linkedin", "email"),
    "LINKEDIN_PASSWORD": ("linkedin", "password"),
    "LINKEDIN_KEYWORDS": ("search", "keywords"),
    "LINKEDIN_LOCATION": ("search", "location"),
    "LINKEDIN_MAX_APPS": ("search", "max_applications"),
    "OPENAI_API_KEY": ("llm", "api_key"),
    "LLM_ENABLED": ("llm", "enabled"),
    "USER_FULLNAME": ("user_profile", "full_name"),
    "USER_PHONE": ("user_profile", "phone"),
    "USER_RESUME": ("user_profile", "resume_path"),
}

class Config:
    def __init__(self, config_file: str = DEFAULT_CONFIG_PATH):
        self.config_file = config_file
        self.data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from a YAML file, then override from environment variables.
        """
        config_data = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

        # Override with environment variables if they exist.
        for env_var, (section, key) in ENV_VAR_MAP.items():
            if os.environ.get(env_var) is not None:
                # Ensure the sub-dict exists
                if section not in config_data:
                    config_data[section] = {}
                raw_value = os.environ[env_var]

                # Try to parse booleans or integers if relevant
                if raw_value.lower() in ["true", "false"]:
                    parsed_value = True if raw_value.lower() == "true" else False
                else:
                    try:
                        parsed_value = int(raw_value)
                    except ValueError:
                        parsed_value = raw_value

                config_data[section][key] = parsed_value

        return config_data

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the root level of the config."""
        return self.data.get(key, default)

    def get_section(self, section: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get an entire configuration section."""
        return self.data.get(section, default or {})

    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """
        Get a nested configuration value using a sequence of keys.
        Example: get_nested("linkedin", "email") -> self.data["linkedin"]["email"]
        
        Args:
            *keys: Variable number of string keys to traverse the config
            default: Value to return if the path doesn't exist
            
        Returns:
            The value at the specified path, or the default if not found
        """
        current = self.data
        for key in keys:
            if not isinstance(current, dict):
                return default
            if key not in current:
                return default
            current = current[key]
        return current
