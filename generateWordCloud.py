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

def generateWc(fonts,fenquencies,username):
    wc=EmojiWordCloud(width=1080,height=720,font_path=fonts,background_color="white",max_font_size=200,max_words=1000)
    wc.generateEmojiWordCloud(fenquencies)
    wc.to_file(f"{username}_wordcloud.png")

def generateWcMask(fonts,fenquencies,username,mask):
    wcMask=EmojiWordCloud(width=1080,height=1080,font_path=fonts,background_color="white",max_font_size=175,max_words=1000,mask=mask)
    wcMask.generateEmojiWordCloud(fenquencies)
    from wordcloud import ImageColorGenerator
    wcMask.recolor(color_func=ImageColorGenerator(mask))
    wcMask.to_file(f"{username}_mask_wordcloud.png")

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

    import numpy as np
    from PIL import Image

    maskImg=Image.open('mask.png').convert('RGBA')
    background=Image.new('RGBA',maskImg.size,(255,255,255,255))#type:ignore
    resultImg=Image.alpha_composite(background,maskImg).convert('RGB')
    mask=np.array(resultImg)

    fonts='./SourceHanSansHWSC-Regular.otf'
    #print(fenquencies)
    from multiprocessing import Process
    p1=Process(target=generateWc,args=(fonts,fenquencies|emojis,username))
    p2=Process(target=generateWcMask,args=(fonts,fenquencies|emojis,username,mask))
    p1.start()
    p2.start()
    p1.join()
    p2.join()

    print("词云已生成并保存")

if __name__ == "__main__":
    s=input()
    generateWordCloud(s)