import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from updater import should_require_launcher_update


def test_requires_launcher_update_when_remote_is_newer():
    assert should_require_launcher_update('2.2.1', '2.2.2') is True


def test_does_not_require_launcher_update_when_versions_match():
    assert should_require_launcher_update('2.2.1', '2.2.1') is False


def test_handles_version_strings_with_prefixes():
    assert should_require_launcher_update('v2.2.1', '2.2.2') is True
