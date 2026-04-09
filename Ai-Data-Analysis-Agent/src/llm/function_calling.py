import json

def parse_json(text):

    try:
        return json.loads(text)
    except:
        print("⚠️ JSON解析失败")
        return None