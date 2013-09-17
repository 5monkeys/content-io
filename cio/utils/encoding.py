def encode_text(text):
    if isinstance(text, str):
        return text
    else:
        return text.encode('utf-8')


def decode_text(text):
    if isinstance(text, unicode):
        return text
    else:
        return text.decode('utf-8')
