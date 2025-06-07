"""
Test Runner Configuration for Django Ninja API v3

Created by: Thunder Wave
Date: 2025-01-08
Project: Triad Docker Base

Custom test runner configuration for comprehensive Django Ninja API testing.
"""

import os
import sys
from django.test.runner import DiscoverRunner
from django.conf import settings


class NinjaAPITestRunner(DiscoverRunner):
    """Custom test runner for Django Ninja API tests."""
    
    def setup_test_environment(self, **kwargs):
        """Set up test environment for API testing."""
        super().setup_test_environment(**kwargs)
        
        # Ensure test database is used
        settings.DATABASES['default']['NAME'] = ':memory:'
        
        # Configure test-specific settings
        settings.DEBUG = False
        settings.ALLOWED_HOSTS = ['testserver', 'localhost']
        
        # Disable logging during tests to reduce noise
        settings.LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'null': {
                    'class': 'logging.NullHandler',
                },
            },
            'root': {
                'handlers': ['null'],
            },
        }
    
    def setup_databases(self, **kwargs):
        """Set up test databases."""
        return super().setup_databases(**kwargs)
    
    def teardown_databases(self, old_config, **kwargs):
        """Clean up test databases."""
        super().teardown_databases(old_config, **kwargs)


def run_unit_tests():
    """Run only unit tests."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    
    import django
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    
    # Run only unit tests
    failures = test_runner.run_tests(['tests.unit'])
    
    if failures:
        sys.exit(1)


def run_integration_tests():
    """Run only integration tests."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    
    import django
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    
    # Run only integration tests
    failures = test_runner.run_tests(['tests.integration'])
    
    if failures:
        sys.exit(1)


def run_all_api_tests():
    """Run all Django Ninja API tests."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    
    import django
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    
    # Run all API tests
    failures = test_runner.run_tests(['tests.unit', 'tests.integration'])
    
    if failures:
        sys.exit(1)
        
    print("\n✅ All Django Ninja API v3 tests passed successfully!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Django Ninja API tests')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    
    args = parser.parse_args()
    
    if args.unit:
        run_unit_tests()
    elif args.integration:
        run_integration_tests()
    else:
        run_all_api_tests() 