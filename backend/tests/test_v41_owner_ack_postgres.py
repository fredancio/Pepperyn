"""New timestamped precontrol on explicitly isolated local PostgreSQL only."""
import json

import test_v41_successor_precontrol_postgres as previous
from test_generic_receipt_v3_postgres import v3sql  # noqa: F401
from test_v40_postgres import sql  # noqa: F401
from sandbox.run_v41_owner_ack_successor import precontrol_sql


def test_timestamped_precontrol_preserves_full_adversarial_matrix(v3sql, monkeypatch):
    monkeypatch.setattr(previous, 'precontrol_sql', precontrol_sql)
    def checked(statement, **kwargs):
        output = v3sql(statement, **kwargs)
        if "'observed_at',statement_timestamp()" in statement:
            report = json.loads(output)
            assert report['observed_at']
            assert report['check_version'] == 'v41-owner-ack-precontrol-1'
        return output
    previous.test_complete_precontrol_single_result_and_adversarial_states(checked)
