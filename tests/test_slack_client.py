import os
from integrations.slack_client import SlackClient


def test_webhook_sends_payload(monkeypatch):
    calls = {}

    def fake_post(url, json=None, headers=None):
        calls['url'] = url
        calls['json'] = json

        class Resp:
            status_code = 200

            def raise_for_status(self):
                pass

        return Resp()

    monkeypatch.setenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/T000/B000/XXX')
    monkeypatch.delenv('SLACK_API_TOKEN', raising=False)
    monkeypatch.setattr('requests.post', fake_post)

    client = SlackClient()
    assert client.send_message('hello world')
    assert calls['url'] == 'https://hooks.slack.com/services/T000/B000/XXX'
    assert calls['json'] == {'text': 'hello world'}


def test_api_token_sends_payload(monkeypatch):
    calls = {}

    def fake_post(url, json=None, headers=None):
        calls['url'] = url
        calls['json'] = json
        calls['headers'] = headers

        class Resp:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {'ok': True}

        return Resp()

    monkeypatch.delenv('SLACK_WEBHOOK_URL', raising=False)
    monkeypatch.setenv('SLACK_API_TOKEN', 'xoxb-test')
    monkeypatch.setenv('SLACK_DEFAULT_CHANNEL', '#general')
    monkeypatch.setattr('requests.post', fake_post)

    client = SlackClient()
    assert client.send_message('hi there')
    assert calls['url'] == 'https://slack.com/api/chat.postMessage'
    assert calls['json'] == {'channel': '#general', 'text': 'hi there'}
    assert calls['headers']['Authorization'] == 'Bearer xoxb-test'
