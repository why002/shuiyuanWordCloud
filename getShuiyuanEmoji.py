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


import asyncio
import aiohttp
import aiofiles
import os

async def asyncDownloadEmoji(session:aiohttp.ClientSession,url:str,name:str,headers:dict):
    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
        
            # 确定文件扩展名
            filepath = os.path.join('emoji', f'{name}.png')

            content=await response.read()
            async with aiofiles.open(filepath, 'wb') as f:
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
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        
        for _, emoji_list in emojis.items():
            for emoji in emoji_list:
                name = emoji["name"]
                url = emoji["url"]
                
                # 检查文件是否已存在
                if os.path.exists(os.path.join('emoji',f'{name}.png')):
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
        isTryGetJson=False
        emojis={}
        while not isTryGetJson:
            try:
                with open("emojis.json","r",encoding="utf-8") as f:
                    emojis=json.load(f)
                break
            except FileNotFoundError:
                if isTryGetJson:
                    getEmojiJson()
                    isTryGetJson=True
                else:
                    raise FileNotFoundError("获取emojis.json失败")
        
        with open("cookie.txt", "r", encoding="utf-8") as f:
            cookie = f.read().strip()
        headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
            "cookie":cookie
        }

        if not os.path.exists('emoji'):
            os.makedirs('emoji')
        asyncio.run(currentDownloadEmoji(emojis,headers,16))

    except Exception as e:
        print("下载表情包失败:", e)


if __name__ =="__main__":
    downloadEmoji()