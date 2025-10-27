from wordcloud import WordCloud
import jieba
import re

def getEmoji(word:str)->tuple[str,dict[str,int]]:
    emojiPattern=re.compile(r':(\w+):')
    emojis:dict[str,int]={}
    ls=emojiPattern.findall(word)
    emojiPattern.sub('',word)
    for e in ls:
        if e in emojis:
            emojis[e]+=1
        else:
            emojis[e]=1
    return word,emojis


def generateWordCloud(word:str):

    word,emojis=getEmoji(word)
    print(emojis)

    ls=jieba.lcut(word)
    fenquencies:dict[str,int]={}

    pattern=re.compile(r'[^\w\u4e00-\u9fa5]')
    numberPattern=re.compile(r'[0-9]')

    for w in ls:
        if pattern.match(w):
            continue
        if numberPattern.match(w):
            continue
        if w=='_':
            continue
        if w in fenquencies:
            fenquencies[w]+=1
        else:
            fenquencies[w]=1

    #print(fenquencies)

    stopwords=['的','了','和','是','我','就','都','而且','也','很','在','有','不']
    wc=WordCloud(width=1080,height=720,font_path="msyh.ttc",background_color="white",stopwords=stopwords,max_font_size=150)
    wc.generate_from_frequencies(fenquencies)
    wc.to_file("wordcloud.png")

if __name__ == "__main__":
    s=input()
    generateWordCloud(s)