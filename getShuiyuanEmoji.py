import requests
import json

def getEmojiJson():
    try:
        with open("cookie.txt", "r", encoding="utf-8") as f:
            cookie = f.read().strip()
        headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
            "cookie":cookie
        }
        response = requests.get("https://shuiyuan.sjtu.edu.cn/emojis.json",headers=headers)
        print(response.status_code)
        json_data = response.json()
        with open("emojis.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        print("成功获取水源表情包并保存到emojis.json")
    except Exception as e:
        print("获取水源表情包失败:",e)

if __name__ =="__main__":
    getEmojiJson()