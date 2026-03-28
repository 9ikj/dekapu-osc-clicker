from pythonosc.udp_client import SimpleUDPClient

from .constants import VRCHAT_OSC_IP, VRCHAT_OSC_PORT


class VRChatOSCClient:
    def __init__(self, host=VRCHAT_OSC_IP, port=VRCHAT_OSC_PORT):
        self._client = SimpleUDPClient(host, port)
        self.host = host
        self.port = port

    def press_use_right(self):
        self._client.send_message("/input/UseRight", 1)

    def release_use_right(self):
        self._client.send_message("/input/UseRight", 0)

    def send_chatbox_message(self, text):
        self._client.send_message("/chatbox/input", [text, True, True])
