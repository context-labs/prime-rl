"""Environment loading utilities with file path support."""

import importlib.util
import logging
from pathlib import Path

import verifiers as vf
from verifiers.envs.environment import Environment


logger = logging.getLogger(__name__)


def load_environment(env_id: str, **env_args) -> Environment:
    """Load environment from file path or package.
    
    If env_id is a file path (ends with .py or exists as a file),
    load the module directly from that file. Otherwise, delegate to
    the standard vf.load_environment().
    
    Args:
        env_id: Either a file path or package identifier
        **env_args: Arguments to pass to the environment's load_environment function
        
    Returns:
        Loaded Environment instance
    """
    # Check if env_id is a file path
    env_path = Path(env_id)
    is_file_path = env_path.suffix == ".py" or (env_path.exists() and env_path.is_file())
    
    if is_file_path:
        # Load from file path
        logger.info(f"Loading environment from file: {env_path.absolute()}")
        if not env_path.exists():
            raise FileNotFoundError(f"Environment file not found: {env_path.absolute()}")
        
        # Create module name from file path
        module_name = env_path.stem
        
        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location(module_name, env_path.absolute())
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load module from {env_path.absolute()}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get and call the load_environment function
            if not hasattr(module, "load_environment"):
                raise AttributeError(
                    f"Module '{module_name}' does not have a 'load_environment' function"
                )
            
            env_load_func = getattr(module, "load_environment")
            env_instance = env_load_func(**env_args)
            
            # Set metadata
            env_instance.env_id = env_instance.env_id or env_id
            env_instance.env_args = env_instance.env_args or env_args
            
            logger.info(f"Successfully loaded environment from file '{env_id}'")
            return env_instance
            
        except Exception as e:
            logger.error(f"Failed to load environment from file {env_path.absolute()}: {str(e)}")
            raise RuntimeError(f"Failed to load environment from file '{env_path}': {str(e)}") from e
    else:
        # Use standard verifiers load_environment for package-based environments
        return vf.load_environment(env_id, **env_args)

