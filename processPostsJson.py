import json
import re

def processRepliesJson(filePath:str):
    with open(filePath,'r',encoding='utf-8') as f:
        data=json.load(f)

    posts:list[str]=[]
    aPattern=re.compile(r'<a.*>[^<>]*</a>')
    emojiPattern=re.compile(r'<img[^>]*title="(:[^:]*:)"[^>]*>')
    for item in data:
        content=item.get('excerpt','')
        content=aPattern.sub('',content)
        while emojiPattern.search(content):
            content=emojiPattern.sub(lambda m:m.group(1),content,1)
        if content and content!='':
            posts.append(content+'\n')

    with open('posts.txt','w',encoding='utf-8') as f:
        for post in posts:
            f.write(post)

if __name__ =="__main__":
    processRepliesJson('example_replies.json')