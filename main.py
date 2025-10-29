import os
import json

if __name__ == "__main__":
    if not os.path.exists('cookie.txt'):
        with open('cookie.txt', 'w', encoding='utf-8') as f:
            f.write(input( "请在此处填写水源的登录 Cookie 信息:\n".strip()))
    if not os.path.exists("emoji"):
        from getShuiyuanEmoji import downloadEmoji
        downloadEmoji()

    username = input("请输入水源用户名: ").strip()
    choice='y'
    if os.path.exists(f"{username}_replies.json"):
        while True:
            choice=input(f"{username}_replies.json 已存在，是否重新获取(y/n)?").lower()
            if choice=='y':
                os.remove(f"{username}_replies.json")
                break
            elif choice=='n':
                break
    if choice=='y':
        since_input = input("请输入开始时间 (YYYY-MM-DD) 或留空: ").strip()
        until_input = input("请输入结束时间 (YYYY-MM-DD) 或留空: ").strip()
        
        from datetime import datetime, timezone
        since_dt = datetime.strptime(since_input, '%Y-%m-%d') if since_input else None
        until_dt = datetime.strptime(until_input, '%Y-%m-%d') if until_input else None
        if since_dt and since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=timezone.utc)
        if until_dt and until_dt.tzinfo is None:
            until_dt = until_dt.replace(tzinfo=timezone.utc)
        
        from getShuiyuanPosts import get_user_replies
        import asyncio

        replies = asyncio.run(get_user_replies(username, since_dt=since_dt, until_dt=until_dt)) 
        print(f"总共获取到 {len(replies)} 条回复。")
        
        # 保存到文件
        with open(f"{username}_replies.json", "w", encoding="utf-8") as f:
            json.dump(replies, f, ensure_ascii=False, indent=4)
        
        print(f"回复已保存到 {username}_replies.json")
    
    from processPostsJson import processRepliesJson
    processRepliesJson(username)
    print(f"回复内容已处理并保存到 {username}_posts.txt")

    from generateWordCloud import generateWordCloud
    with open(f"{username}_posts.txt", 'r', encoding='utf-8') as f:
        content=f.read()
    generateWordCloud(content,username)
