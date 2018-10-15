#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

import mock
import pytest
from blinker import signal
from requests.auth import AuthBase

from fiaas_deploy_daemon import Configuration
from fiaas_deploy_daemon.deployer.bookkeeper import DEPLOY_FAILED, DEPLOY_STARTED, DEPLOY_SUCCESS
from fiaas_deploy_daemon.usage_reporting import DevhoseDeploymentEventTransformer
from fiaas_deploy_daemon.usage_reporting.usage_reporter import UsageReporter, UsageEvent


class TestUsageReporter(object):
    @pytest.fixture
    def config(self):
        config = mock.create_autospec(Configuration([]), spec_set=True)
        config.usage_reporting_endpoint = "http://example.com/usage"
        return config

    @pytest.fixture
    def mock_transformer(self, config):
        return mock.create_autospec(DevhoseDeploymentEventTransformer(config))

    @pytest.fixture
    def mock_session(self):
        return mock.NonCallableMagicMock()

    @pytest.fixture
    def mock_auth(self):
        return mock.create_autospec(AuthBase())

    @pytest.mark.parametrize("signal_name", (DEPLOY_STARTED, DEPLOY_FAILED, DEPLOY_SUCCESS))
    def test_signal_to_event(self, config, mock_transformer, mock_session, mock_auth, signal_name, app_spec):
        reporter = UsageReporter(config, mock_transformer, mock_session, mock_auth)

        signal(signal_name).send(app_spec=app_spec)

        event = reporter._event_queue.get_nowait()

        assert event.status == signal_name.split("_")[-1].upper()
        assert event.app_spec == app_spec

    def test_event_to_transformer(self, config, mock_transformer, mock_session, mock_auth):
        event = UsageEvent("status", object())
        reporter = UsageReporter(config, mock_transformer, mock_session, mock_auth)
        reporter._event_queue = [event]

        reporter()

        mock_transformer.assert_called_once_with(event.status, event.app_spec)

    def test_post_to_webhook(self, config, mock_transformer, mock_session, mock_auth):
        event = UsageEvent("status", object())
        reporter = UsageReporter(config, mock_transformer, mock_session, mock_auth)
        reporter._event_queue = [event]

        payload = {"dummy": "payload"}
        mock_transformer.return_value = payload

        reporter()

        mock_session.post.assert_called_once_with(config.usage_reporting_endpoint, json=payload, auth=mock_auth)