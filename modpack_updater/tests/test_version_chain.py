import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from updater import collect_pending_updates


def test_collect_pending_updates_from_chain():
    remote_data = {
        'updates': [
            {'from_version': '2.4.3', 'to_version': '2.4.4'},
            {'from_version': '2.4.4', 'to_version': '2.4.5'}
        ]
    }

    updates = collect_pending_updates('2.4.3', remote_data)
    assert [item['to_version'] for item in updates] == ['2.4.4', '2.4.5']


def test_collect_pending_updates_falls_back_to_legacy_single_update():
    remote_data = {
        'modpack_version': '2.4.4'
    }

    updates = collect_pending_updates('2.4.3', remote_data)
    assert len(updates) == 1
    assert updates[0]['to_version'] == '2.4.4'


def test_collect_pending_updates_bootstraps_missing_version_to_fixed_release():
    remote_data = {
        'modpack_version': '2.4.5',
        'bootstrap_version': '2.4.4',
        'update_chain': [
            {'from_version': '2.4.3', 'to_version': '2.4.4'},
            {'from_version': '2.4.4', 'to_version': '2.4.5'}
        ]
    }

    updates = collect_pending_updates('0.0.0', remote_data)
    assert [item['to_version'] for item in updates] == ['2.4.4', '2.4.5']
