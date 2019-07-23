import os
import re
import time
import json
import urllib
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen

def UrlOpen(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent',
                   'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36 LBBROWSER')
    response = urllib.request.urlopen(req)
    html = response.read()
    return html

def parsebookhtml(url,starturl):
    '''
    获取所有小说的链接和对应的题目
    '''
    html=urlopen(url).read()
    soup=BeautifulSoup(html,features='lxml')
    books={}
    novellist=soup.find_all('div',{'class':'novellist'})
    for novels in novellist:
        novel=novels.find_all('a')
        if not novel:
            continue
        for book in novel:
            link=starturl+book['href']
            title=book.get_text()
            if title not in books:
                books[title]=link
    return books

def parsecataloguehtml(url,starturl):
    '''
    获取某本小说每一章的链接
    '''
    html=urlopen(url).read()
    soup=BeautifulSoup(html,features='lxml')
    #title=soup.find('div',{'id':'info'})
    #title=title.find('h1')
    #title=title.get_text()

    seclinks=set()
    section=soup.find_all('dd')
    for sec in section:
        link=sec.find('a')
        if not link:
            continue
        link=starturl+sec.find('a')['href']
        seclinks.add(link)
    return list(seclinks)#,title

def parsenovelhtml(url):
    '''
    获取当前页面的小说内容
    返回包含标签和文本的字典
    '''
    html=urlopen(url).read()
    time.sleep(0.1)
    soup=BeautifulSoup(html,features='lxml')
    texts=''
    labels=['网络小说']
    label=soup.find_all('a',{'href':re.compile('.*?xiaoshuo')})[0]
    labels.append(label.get_text())
    contents=soup.find_all('div',{'id':'content'})[0]
    contents=contents.find_all('p')
    for text in contents:
        texts+=text.get_text()
        texts+='\n'
    artical={}
    artical['labels']=labels
    artical['text']=texts
    return artical

if __name__=='__main__':
    bqgurl='https://www.bqg5.cc/'
    nurl='https://www.bqg5.cc/1_1399/740420.html'
    catalogueurl='https://www.bqg5.cc/1_1399/'
    booksurl='https://www.bqg5.cc/quanbuxiaoshuo/'

    if os.path.exists('data/titles.txt'):
        with open('data/titles.txt') as fin:
            titles=fin.read()
        titles=set(titles.split(' '))
    else:
        titles=set()
    books=parsebookhtml(booksurl,bqgurl)
    nbook=0
    for title in books:
        if title in titles:
            continue
        titles.add(title)
        link=books[title]
        seclinks=parsecataloguehtml(link,bqgurl)#某本书所有章节的链接
        articals=[]
        count=0
        for seclink in seclinks:
            articals.append(parsenovelhtml(seclink))
            count+=1
            if count%200==0:
                print('get two hundred')
        if not articals:
            continue
        file_path='novels/'+title+'.json'
        with open(file_path,'w',encoding='utf-8') as fout:
            json.dump(articals,fout)
        print(title+' download success')
        nbook+=1
        if nbook%10==0:
            temp=(' ').join(list(titles))
            with open('data/titles.txt','w',encoding='utf-8') as fout:
                fout.write(temp)
    titles=(' ').join(list(titles))
    with open('data/titles.txt','w',encoding='utf-8') as fout:
        fout.write(titles)



