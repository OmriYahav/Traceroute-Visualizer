from traceroute_visualizer.services import traceroute_service


class Packet:
    def __init__(self, ttl=None, src=None, sent_time=None, time=None):
        self.ttl = ttl
        self.src = src
        self.sent_time = sent_time
        self.time = time


def test_run_traceroute_output_shape(monkeypatch):
    answered = [
        (Packet(ttl=1, sent_time=1.0), Packet(src="1.1.1.1", time=1.02)),
        (Packet(ttl=3, sent_time=2.0), Packet(src="3.3.3.3", time=2.03)),
    ]

    def fake_traceroute(*args, **kwargs):
        return answered, []

    monkeypatch.setattr(traceroute_service, "traceroute", fake_traceroute)
    hops = traceroute_service.run_traceroute(
        "example.com", max_hops=3, timeout=1, retries=0
    )

    assert len(hops) == 3
    assert hops[0]["ip"] == "1.1.1.1"
    assert hops[1]["status"] == "timeout"
    assert hops[2]["ip"] == "3.3.3.3"
