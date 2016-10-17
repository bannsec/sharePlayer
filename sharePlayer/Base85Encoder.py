import base64

class Base85Encoder(object):

    @staticmethod
    def encode(data):
        return base64.b85encode(data)

    @staticmethod
    def decode(data):
        # Strip any newlines...
        return base64.b85decode(data.strip(b"\n"))
