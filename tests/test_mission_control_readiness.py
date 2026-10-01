"""Real-response readiness semantics, plus wiring; fixtures are test data only."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mc_readiness',ROOT/'tests/mission_control_self_test_runner.py')
assert spec is not None and spec.loader is not None
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class DemoIndexReadinessTests(unittest.TestCase):
    def test_signing_guard_uses_the_test_only_runner(self):
        self.assertIn('mission_control_self_test_runner.py',(ROOT/'tests/test_mission_control_signing.py').read_text())
    def test_waits_for_actual_ready_result(self):
        replies=iter([(200,{'notes':[]}),(200,{'notes':[1,2]}),(200,{'notes':[1,2,3,4]})])
        get=runner.with_demo_index_readiness(lambda *args:next(replies),timeout=1)
        self.assertEqual(get('/api/memory',1),(200,{'notes':[1,2,3,4]}))
    def test_timeout_preserves_actual_empty_result(self):
        get=runner.with_demo_index_readiness(lambda *args:(200,{'notes':[]}),timeout=0.01)
        self.assertEqual(get('/api/memory',1),(200,{'notes':[]}))
    def test_http_error_is_not_hidden(self):
        get=runner.with_demo_index_readiness(lambda *args:(500,{'error':'collector unavailable'}))
        self.assertEqual(get('/api/memory',1),(500,{'error':'collector unavailable'}))
    def test_rehearsal_retries_only_known_index_race(self):
        from types import SimpleNamespace
        failure=SimpleNamespace(returncode=1,stdout='vault index populated from the demo vault',stderr='IndexError: list index out of range')
        success=SimpleNamespace(returncode=0,stdout='REHEARSAL PASSED',stderr='')
        replies=iter([failure,success])
        self.assertIs(runner.retry_demo_index_rehearsal(lambda:next(replies)),success)
    def test_rehearsal_exhaustion_retains_failure(self):
        from types import SimpleNamespace
        failure=SimpleNamespace(returncode=1,stdout='vault index populated from the demo vault',stderr='IndexError: list index out of range')
        calls=[]
        def invoke():calls.append(1);return failure
        self.assertIs(runner.retry_demo_index_rehearsal(invoke),failure)
        self.assertEqual(len(calls),3)
    def test_rehearsal_does_not_retry_unrelated_failure(self):
        from types import SimpleNamespace
        failure=SimpleNamespace(returncode=1,stdout='',stderr='invalid signature')
        calls=[]
        def invoke():calls.append(1);return failure
        self.assertIs(runner.retry_demo_index_rehearsal(invoke),failure)
        self.assertEqual(len(calls),1)
    def test_only_initial_memory_read_is_delayed(self):
        replies=iter([(200,{'health':'up'}),(200,{'notes':[1,2,3,4]}),(200,{'notes':[]})])
        get=runner.with_demo_index_readiness(lambda *args:next(replies),timeout=1)
        self.assertEqual(get('/api/health',1),(200,{'health':'up'}))
        self.assertEqual(get('/api/memory',1),(200,{'notes':[1,2,3,4]}))
        self.assertEqual(get('/api/memory',1),(200,{'notes':[]}))

if __name__=='__main__':unittest.main()
