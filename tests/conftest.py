"""Re-export this device's fixtures and enable the custom integration."""

import pytest

from .moduletwo_fixtures import entry, mock_client, registers  # noqa: F401


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Enable the generated custom integration in the test runtime."""
