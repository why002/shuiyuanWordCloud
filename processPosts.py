import json
import re

def processRepliesJson(userName:str):
    with open(f'{userName}_replies.json','r',encoding='utf-8') as f:
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

    with open(f'{userName}_posts.txt','w',encoding='utf-8') as f:
        for post in posts:
            f.write(post)

def processTopic(topic:int):
    with open(f'{topic}_origin.txt','r',encoding='utf-8') as f:
        text=f.read()
    text=text.replace('-------------------------','')
    text=text.replace('---','')

    imgPattern=re.compile(r'!\[[^\]\n]*\]\([^\)]*\)')
    text=imgPattern.sub('',text)

    urlPattern=re.compile(r'\[([^\]\n]*)\]\([^\)]*\)')
    while urlPattern.search(text):
        text=urlPattern.sub(lambda m:m.group(1),text,1)
    
    urlPattern2=re.compile(r'https?://[^\s]*')
    text=urlPattern2.sub('',text)

    bbcodePattern=re.compile(r'\[[^\]\n]*\]')
    text=bbcodePattern.sub('',text)

    htmlPattern=re.compile(r'<[^>\n]*>')
    text=htmlPattern.sub('',text)

    postPattern=re.compile(r'[^|\n]*\| \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC \| #\d+')
    text=postPattern.sub('',text)

    newlinePattern=re.compile(r'[\n]{2,}')
    text=newlinePattern.sub('\n',text)

    with open(f'{topic}_processed.txt','w',encoding='utf-8') as f:
        f.write(text)
    
    
if __name__ =="__main__":
    processTopic(429045)