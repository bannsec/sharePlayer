import base64

class Base85Encoder(object):

    @staticmethod
    def encode(data):
        return base64.b85encode(data)

    @staticmethod
    def decode(data):
        return base64.b85decode(data)
