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
    解析全部小说页，获取所有小说的链接和对应的题目
    '''
    html=UrlOpen(url)
    time.sleep(0.1)
    soup=BeautifulSoup(html,features='lxml')
    books={}
    novellist=soup.find('div',{'id':'right'})
    novels=novellist.find_all('li')
    for novel in novels:
        book=novel.find('p').find('a')
        link=starturl+book['href']
        title=book.get_text()
        if title not in books:
            books[title]=link
    return books

def parsecataloguehtml(url,starturl):
    '''
    获取某本小说每一章的链接
    '''
    html=UrlOpen(url)
    time.sleep(0.1)
    soup=BeautifulSoup(html,features='lxml')
    seclinks=set()
    sections=soup.find('div',{'class':'lb'})
    sections=sections.find_all('li')
    for sec in sections:
        sec=sec.find('a')
        link=sec['href']
        if not link:
            continue
        link=starturl+link
        seclinks.add(link)
    return list(seclinks)

def parsenovelhtml(url):
    '''
    获取当前页面的小说内容
    返回包含标签和文本的字典
    '''
    html=UrlOpen(url)
    time.sleep(0.3)
    soup=BeautifulSoup(html,features='lxml')
    labels=['古龙','武侠小说']
    title=soup.find('h1',{'class':'mulu'})
    title=title.get_text()
    texts=title+'\n'
    contents=soup.find('div',{'class':'nr_con'})
    contents=contents.find_all('p')
    for content in contents:
        texts+=content.get_text()
        texts+='\n'
    artical={}
    artical['labels']=labels
    artical['text']=texts
    return artical

if __name__=='__main__':
    glurl='https://www.gulongwang.com/'
    booksurl='https://www.gulongwang.com/'

    if os.path.exists('D:\\项目\\成语分级\\语料\\data\\titles.txt'):
        with open('D:\\项目\\成语分级\\语料\\data\\titles.txt',encoding='utf-8') as fin:
            titles=fin.read()
        titles=set(titles.split(' '))
    else:
        titles=set()
    books=parsebookhtml(booksurl,glurl)
    #nbook=0
    for title in books:
        if title in titles:
            print("重复小说")
            continue
        titles.add(title)
        link=books[title]
        seclinks=parsecataloguehtml(link,glurl)#某本书所有章节的链接
        articals=[]
        count=0
        for seclink in seclinks:
            articals.append(parsenovelhtml(seclink))
            count+=1
            if count%200==0:
                print('get two hundred')
        if not articals:
            continue
        file_path='D:\\项目\\成语分级\\语料\\novels\\'+title+'.json'
        with open(file_path,'w',encoding='utf-8') as fout:
            json.dump(articals,fout)
        print(title+' download success')
        with open('D:\\项目\\成语分级\\语料\\data\\titles.txt','a',encoding='utf-8') as fout:
            fout.write(title+' ')