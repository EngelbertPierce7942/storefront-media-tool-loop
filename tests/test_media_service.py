from media_service import MediaRequest, run_media_loop


class FakeFunction:
    def __init__(self, name):
        self.name = name


class FakeCall:
    def __init__(self, name, ident):
        self.id = ident
        self.function = FakeFunction(name)

    def model_dump(self):
        return {"id": self.id, "type": "function", "function": {"name": self.function.name, "arguments": "{}"}}


class FakeMessage:
    content = None

    def __init__(self, calls):
        self.tool_calls = calls


class FakeResponse:
    def __init__(self, message):
        self.choices = [type("Choice", (), {"message": message})()]


class FakeCompletions:
    def __init__(self):
        self.calls = [[FakeCall("ingest_asset", "1")], [FakeCall("create_processing_job", "2")], [FakeCall("deliver_to_creator", "3")], []]

    def create(self, **kwargs):
        return FakeResponse(FakeMessage(self.calls.pop(0)))


class FakeClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeCompletions()})()


def test_media_loop_delivers_only_after_all_tools():
    result = run_media_loop(MediaRequest(asset_id="a1", storefront="shop", creator_email="c@example.com"), FakeClient())
    assert result.status == "delivered"
    assert result.download_name == "a1.mp4"
