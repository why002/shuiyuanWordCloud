import asyncio
import io
import json
import os
import sys
from urllib.parse import urlsplit

import aiofiles
import aiohttp
import requests
from PIL import Image

try:
    import cairosvg
except ImportError:
    cairosvg = None

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        # 部分表情名含 ñ 等 GBK 无法编码的字符，避免 print 抛异常中断下载
        stream.reconfigure(errors="replace")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"


def readCookie():
    with open("cookie.txt", "r", encoding="utf-8") as f:
        return f.read().strip()


def getEmojiJson():
    headers = {
        "user-agent": USER_AGENT,
        "cookie": readCookie()
    }
    response = requests.get("https://shuiyuan.sjtu.edu.cn/emojis.json", headers=headers, timeout=30)
    if response.status_code != 200:
        raise Exception(f"请求失败，状态码: {response.status_code}")
    json_data = response.json()
    with open("emojis.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
    print("成功获取水源表情包并保存到emojis.json")


def emojiExt(url: str) -> str:
    ext = os.path.splitext(urlsplit(url).path)[1].lower()
    return ext or ".png"


def isUsableEmoji(filepath: str) -> bool:
    if not os.path.exists(filepath):
        return False
    with open(filepath, "rb") as f:
        head = f.read(256)
    # 旧版本会把 SVG 内容直接存成 .png，PIL 无法打开，需要重新下载转换
    if head.lstrip().startswith(b"<?xml") or b"<svg" in head:
        return False
    return True


async def asyncDownloadEmoji(session: aiohttp.ClientSession, url: str, name: str, headers: dict):
    filepath = os.path.join("emoji", f"{name}.png")
    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            content = await response.read()

        ext = emojiExt(url)
        if ext == ".svg":
            if cairosvg is None:
                raise RuntimeError("未安装 cairosvg，无法转换 SVG")
            content = cairosvg.svg2png(bytestring=content, output_width=256)
        elif ext != ".png":
            # webp/jpeg 等格式统一转成 PNG，保证下游 PIL 能直接打开
            with Image.open(io.BytesIO(content)) as img:
                buf = io.BytesIO()
                img.convert("RGBA").save(buf, format="PNG")
                content = buf.getvalue()

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

        print(f"成功下载表情 {name}")
    except Exception as e:
        print(f"下载表情 {name} 失败: {e}")

async def currentDownloadEmoji(emojis:dict,headers:dict,maxConcurrent:int=8):
    # 创建信号量限制并发数量
    semaphore = asyncio.Semaphore(maxConcurrent)
    
    async def bounded_download(session, url, name, headers):
        async with semaphore:
            await asyncDownloadEmoji(session, url, name, headers)
    
    connector = aiohttp.TCPConnector(limit=maxConcurrent)  # 限制TCP连接数
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        
        for _, emoji_list in emojis.items():
            for emoji in emoji_list:
                name = emoji["name"]
                url = emoji["url"]
                
                # 检查文件是否已存在且可用
                if isUsableEmoji(os.path.join('emoji',f'{name}.png')):
                    print(f"表情 {name} 已存在，跳过下载")
                    continue

                # URL处理
                if url.startswith("//"):
                    url = "https:" + url
                elif url.startswith("/"):
                    url = "https://shuiyuan.sjtu.edu.cn" + url
                
                # 创建下载任务
                task = asyncio.create_task(bounded_download(session, url, name, headers))
                tasks.append(task)
                print(f"开始下载表情 {name}, 当前任务数: {len(tasks)}")
                # 添加小延迟避免瞬间创建过多任务
                await asyncio.sleep(0.01)
        
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)

def downloadEmoji():
    try:
        # 每次运行先刷新表情列表，避免本地缓存里的旧 URL 失效（如 google）
        try:
            getEmojiJson()
        except Exception as e:
            print("获取最新表情列表失败，使用本地 emojis.json:", e)

        with open("emojis.json", "r", encoding="utf-8") as f:
            emojis = json.load(f)

        with open("cookie.txt", "r", encoding="utf-8") as f:
            cookie = f.read().strip()
        headers={
            "user-agent": USER_AGENT,
            "cookie":cookie
        }

        if not os.path.exists('emoji'):
            os.makedirs('emoji')
        asyncio.run(currentDownloadEmoji(emojis,headers,16))

    except Exception as e:
        print("下载表情包失败:", e)


if __name__ =="__main__":
    downloadEmoji()