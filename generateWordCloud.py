from emojiWordCloud import EmojiWordCloud
import jieba
import re

def getEmoji(word:str)->tuple[str,dict[str,int]]:
    emojiPattern=re.compile(r'(:\w+:)')
    emojis:dict[str,int]={}
    ls=emojiPattern.findall(word)
    word=emojiPattern.sub('',word)
    for e in ls:
        if e in emojis:
            emojis[e]+=1
        else:
            emojis[e]=1
    return word,emojis


def generateWordCloud(word:str,username:str=''):

    word,emojis=getEmoji(word)
    #print(emojis)

    ls=jieba.lcut(word)
    fenquencies:dict[str,int]={}

    pattern=re.compile(r'[^\w\u4e00-\u9fa5]')
    numberPattern=re.compile(r'[0-9]')
    stopwords:set[str]=set()
    import os
    if os.path.exists('stopwords.txt'):
        with open('stopwords.txt','r',encoding='utf-8') as f:
            stopwords=set([line.strip() for line in f.readlines()])
    for w in ls:
        if pattern.match(w):
            continue
        if numberPattern.match(w):
            continue
        if w=='_':
            continue
        if w in stopwords:
            continue
        if w in fenquencies:
            fenquencies[w]+=1
        else:
            fenquencies[w]=1

    #print(fenquencies)
    try:
        wc=EmojiWordCloud(width=1080,height=720,font_path="msyh.ttc",background_color="white",stopwords=stopwords,max_font_size=200,max_words=1000)
    except Exception as e:
        try:
            wc=EmojiWordCloud(width=1080,height=720,font_path="pingfang SC",background_color="white",stopwords=stopwords,max_font_size=200,max_words=1000)
        except Exception as e:
            print("错误: 未找到合适的字体文件")
            return
    wc.generateEmojiWordCloud(fenquencies|emojis)
    wc.to_file(f"{username}_wordcloud.png")

if __name__ == "__main__":
    s=input()
    generateWordCloud(s)