from json import loads


def request(event):
    try:
        inputs = event["body"] or None
        if inputs is not None:
            return loads(inputs)
        else:
            return None
    except Exception as e:
        print(str(e))
        return None
