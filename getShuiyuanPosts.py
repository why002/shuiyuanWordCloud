import aiohttp
import asyncio
from datetime import datetime,timezone
import json

def parse_iso_datetime(dt_str: str) -> datetime|None:
    try:
        # Discourse 返回类似 2024-05-12T03:14:15.000Z
        return datetime.strptime(dt_str.replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S.%f%z')
    except Exception:
        try:
            return datetime.strptime(dt_str.replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S%z')
        except Exception:
            return None
        
async def get_user_replies(username: str, max_pages:int|None = None,
                          since_dt: datetime|None = None,
                          until_dt: datetime|None = None) -> list[dict]:
    """
    异步获取指定用户的所有回复
    
    Args:
        username: 用户名
        max_pages: 最大页数，None 表示获取所有
        
    Returns:
        回复列表
    """
    print(f'正在异步获取用户 @{username} 的回复...')
    
    all_replies = []
    offset = 0
    page = 1
    
    # 读取cookie（同步操作，因为文件很小）
    try:
        with open("cookie.txt", "r", encoding="utf-8") as f:
            cookie = f.read().strip()
    except FileNotFoundError:
        print("错误: 未找到 cookie.txt 文件")
        return []
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "cookie": cookie
    }
    
    # 创建异步会话
    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            if max_pages and page > max_pages:
                break
                
            # filter=5 表示 replies (回复)
            url = f"https://shuiyuan.sjtu.edu.cn/user_actions.json?username={username}&filter=5&offset={offset}"
            
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"请求失败: {response.status if response else 'Network Error'}")
                        break
                        
                    data = await response.json()
                    user_actions = data.get('user_actions', [])
                    
                    if not user_actions:
                        print(f"已获取所有回复，共 {len(all_replies)} 条")
                        break
                    
                    # 过滤时间窗口
                    filtered_actions = []
                    page_times = []
                    for ua in user_actions:
                        c = ua.get('created_at')
                        cdt = parse_iso_datetime(c) if c else None
                        if cdt:
                            page_times.append(cdt)
                        # 应用窗口：since <= cdt <= until
                        if cdt:
                            if since_dt and cdt < since_dt:
                                continue
                            if until_dt and cdt > until_dt:
                                continue
                        filtered_actions.append(ua)

                    all_replies.extend(filtered_actions)
                    print(f"第 {page} 页: 获取了 {len(user_actions)} 条，窗口内 {len(filtered_actions)} 条 (累计 {len(all_replies)} 条)")

                    # 提前停止条件：页面最老时间 < since_dt
                    if since_dt and page_times:
                        oldest_on_page = min(page_times)
                        if oldest_on_page < since_dt:
                            print("达到开始时间阈值，停止翻页。")
                            break
                    
                    offset += 30
                    page += 1
                    
                    # 添加小延迟避免请求过快
                    await asyncio.sleep(0.3)
                    
            except Exception as e:
                print(f"获取第 {page} 页时出错: {e}")
                break
    
    return all_replies

if __name__ == "__main__":
    username = input("请输入水源用户名: ").strip()
    since_input = input("请输入开始时间 (YYYY-MM-DD) 或留空: ").strip()
    until_input = input("请输入结束时间 (YYYY-MM-DD) 或留空: ").strip()
    
    since_dt = datetime.strptime(since_input, '%Y-%m-%d') if since_input else None
    until_dt = datetime.strptime(until_input, '%Y-%m-%d') if until_input else None
    if since_dt and since_dt.tzinfo is None:
        since_dt = since_dt.replace(tzinfo=timezone.utc)
    if until_dt and until_dt.tzinfo is None:
        until_dt = until_dt.replace(tzinfo=timezone.utc)
    replies = asyncio.run(get_user_replies(username, since_dt=since_dt, until_dt=until_dt)) 
    print(f"总共获取到 {len(replies)} 条回复。")
    
    # 保存到文件
    with open(f"{username}_replies.json", "w", encoding="utf-8") as f:
        json.dump(replies, f, ensure_ascii=False, indent=4)
    
    print(f"回复已保存到 {username}_replies.json")