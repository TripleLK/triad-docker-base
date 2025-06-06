#!/usr/bin/env python3
"""
Environment Switching Utility

This script allows easy switching between different database environments
by creating a symlink to the appropriate .env file.

Usage:
    python tools/switch_env.py [dev|prod|safari] [mac|ec2]
"""
import os
import sys
import argparse
from pathlib import Path

def switch_environment(env_type, platform):
    """
    Switch between different environments by creating a symlink to the appropriate .env file
    
    Args:
        env_type: 'dev', 'prod', or 'safari'
        platform: 'mac' or 'ec2'
    """
    base_dir = Path(__file__).resolve().parent.parent
    envs_dir = base_dir / "envs"
    
    # Map environment types to their files
    env_files = {
        'dev-mac': envs_dir / "dev.mac.env",
        'prod-mac': envs_dir / "prod.mac.env", 
        'safari-mac': envs_dir / "dev.safari.env",
        'dev-ec2': envs_dir / "dev.ec2.env",
        'prod-ec2': envs_dir / "prod.ec2.env"
    }
    
    env_key = f"{env_type}-{platform}"
    if env_key not in env_files:
        print(f"Error: Unknown environment '{env_type}' for platform '{platform}'.")
        print(f"Valid combinations: dev-mac, prod-mac, safari-mac, dev-ec2, prod-ec2")
        return False
    
    env_file = env_files[env_key]
    env_link = base_dir / ".env"
    
    # Remove existing symlink if it exists
    if env_link.exists() or env_link.is_symlink():
        os.unlink(env_link)
    
    # Create new symlink
    os.symlink(env_file, env_link)
    
    print(f"Switched to {env_type} environment on {platform}. Using {env_file.name}")
    
    # Print database info based on environment
    if env_type in ['dev', 'safari']:
        print("Using SQLite database")
    else:
        print("Using PostgreSQL database - make sure PostgreSQL is running")
    
    # Clear instructions
    print("\nIMPORTANT: If you have set DJANGO_ENV or DJANGO_SETTINGS_MODULE in your")
    print("shell environment, they will override the .env file. To ensure the changes")
    print("take effect, unset these variables before running Django commands:")
    print("  unset DJANGO_ENV DJANGO_SETTINGS_MODULE")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Switch between development and production environments")
    parser.add_argument("environment", choices=["dev", "prod", "safari"], 
                        help="Environment to switch to (dev, prod, or safari)")
    parser.add_argument("platform", choices=["mac", "ec2"], default="mac", nargs="?",
                        help="Platform to use (mac or ec2)")
    
    args = parser.parse_args()
    switch_environment(args.environment, args.platform) 