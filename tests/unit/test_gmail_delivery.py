import base64

from iceflo_signal.delivery.gmail import GmailSender


class FakeExecute:
    def execute(self):
        return {"id": "msg-123", "threadId": "thread-456"}


class FakeMessages:
    def __init__(self):
        self.body = None
        self.user_id = None

    def send(self, userId, body):
        self.user_id = userId
        self.body = body
        return FakeExecute()


class FakeUsers:
    def __init__(self, messages):
        self._messages = messages

    def messages(self):
        return self._messages


class FakeService:
    def __init__(self):
        self.messages_resource = FakeMessages()

    def users(self):
        return FakeUsers(self.messages_resource)


def test_gmail_sender_sends_base64url_encoded_raw_message() -> None:
    sender = GmailSender.__new__(GmailSender)
    sender._service = FakeService()
    sender._user_id = "me"

    result = sender.send_raw_message("To: test@example.com\nSubject: Hi\n\nBody")

    body = sender._service.messages_resource.body
    assert result.message_id == "msg-123"
    assert sender._service.messages_resource.user_id == "me"
    assert base64.urlsafe_b64decode(body["raw"]).decode("utf-8") == "To: test@example.com\nSubject: Hi\n\nBody"
