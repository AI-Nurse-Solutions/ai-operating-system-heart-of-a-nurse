# Copyright 2026 Robert Domondon
# SPDX-License-Identifier: Apache-2.0
"""Authenticated personal capture uses shared writers, never page identity."""
from test_app import _AppCase


class CaptureHttpTests(_AppCase):
    def setUp(self):
        super().setUp()
        self.envelope('/ipc/init', 'POST', {'name': 'Synthetic planning', 'owner': 'me'})

    def test_project_can_be_captured_from_empty_workspace(self):
        envelope = self.envelope('/ipc/project-add', 'POST', {
            'title': 'Practice project', 'purpose': 'Public planning exercise', 'owner_role': 'me'})
        self.assertTrue(envelope['ok'], envelope)
        project = envelope['data']['id']
        home = self.envelope('/ipc/mission')['data']
        self.assertEqual(home['projects_in_motion']['items'][0]['id'], project)

    def test_refused_capture_has_no_record_or_audit_effect(self):
        from nurse_manager.services import ManagerWorkspace
        with_ws = ManagerWorkspace(self.app.workspace)
        try:
            before = [dict(row) for row in with_ws.store.events()]
            envelope = self.envelope('/ipc/project-add', 'POST', {
                'title': 'Contact 555-867-5309', 'purpose': 'Practice', 'owner_role': 'me'})
            self.assertFalse(envelope['ok'])
            self.assertEqual(envelope['error']['type'], 'CaptureRefused')
            self.assertEqual(with_ws.store.conn.execute('SELECT count(*) FROM projects').fetchone()[0], 0)
            self.assertEqual([dict(row) for row in with_ws.store.events()], before)
        finally:
            with_ws.close()

    def capture(self):
        return self.envelope('/ipc/capture')['data']

    def test_shared_records_transitions_and_stale_refusal(self):
        project = self.envelope('/ipc/project-add', 'POST', {
            'title': 'Outline practice', 'purpose': 'Public exercise', 'owner_role': 'Manager'})['data']['id']
        task = self.envelope('/ipc/task-add', 'POST', {'title': 'Review outline',
            'project_id': project, 'owner_role': 'me', 'reviewer_role': 'Reviewer', 'status': 'ready'})['data']['task']['id']
        decision = self.envelope('/ipc/decision-add', 'POST', {'question': 'Which outline?',
            'decision': 'Short outline', 'decision_role': 'Council', 'decided_on': '2026-10-04',
            'project_id': project})
        self.assertTrue(decision['ok'], decision)
        data = self.capture()
        self.assertEqual(data['tasks'][0]['id'], task)
        self.assertEqual(data['decisions'][0]['decided_by'], 'Council')
        self.assertTrue(self.envelope('/ipc/task-complete', 'POST', {'id': task,
            'expected_status': 'ready', 'evidence': 'Public outline checked'})['ok'])
        stale = self.envelope('/ipc/task-move', 'POST', {'id': task,
            'expected_status': 'ready', 'status': 'in_progress'})
        self.assertFalse(stale['ok'])
        self.assertEqual(self.capture()['tasks'][0]['status'], 'completed')
        self.assertFalse(self.envelope('/ipc/task-reopen', 'POST', {'id': task,
            'expected_status': 'completed', 'status': 'ready', 'reason': ''})['ok'])
        self.assertTrue(self.envelope('/ipc/task-reopen', 'POST', {'id': task,
            'expected_status': 'completed', 'status': 'ready', 'reason': 'Practice again'})['ok'])
        self.assertTrue(self.envelope('/ipc/task-withdraw', 'POST', {'id': task,
            'expected_status': 'ready', 'reason': 'Practice finished'})['ok'])
        self.assertEqual(self.capture()['tasks'][0]['status'], 'withdrawn')

    def test_priority_compare_and_swap_preserves_newer_list_and_events(self):
        from nurse_manager.services import ManagerWorkspace
        old = self.capture()
        body = {'week': old['week_of'], 'expected_sha256': old['priorities_sha256'],
                'replace_priorities': True, 'item_1': 'Review public outline'}
        self.assertTrue(self.envelope('/ipc/priorities-set', 'POST', body)['ok'])
        ws = ManagerWorkspace(self.app.workspace)
        try:
            before = [dict(row) for row in ws.store.events()]
            stale = self.envelope('/ipc/priorities-set', 'POST', {**body, 'item_1': 'Old tab proposal'})
            self.assertFalse(stale['ok'])
            self.assertIn('priorities changed', stale['error']['message'])
            self.assertEqual(self.capture()['priorities'][0]['text'], 'Review public outline')
            self.assertEqual([dict(row) for row in ws.store.events()], before)
            self.assertEqual(self.request('/ipc/priorities-set', 'POST', {**body, 'replace_priorities': 'yes'})[0], 400)
        finally:
            ws.close()

    def test_roles_and_oversize_captures_cannot_mutate_records(self):
        self.assertFalse(self.envelope('/ipc/project-add', 'POST', {
            'title': 'Practice', 'purpose': 'Public outline', 'owner_role': 'Unapproved personal name'})['ok'])
        self.assertEqual(self.request('/ipc/project-add', 'POST', {
            'title': 'x' * 201, 'purpose': 'Practice', 'owner_role': 'me'})[0], 400)
        self.assertFalse(self.envelope('/ipc/task-add', 'POST', {
            'title': 'Practice', 'project_id': 'prj-' + 'a' * 12, 'owner_role': 'me'})['ok'])
        self.assertEqual(self.capture()['projects'], [])
        self.assertEqual(self.capture()['tasks'], [])
