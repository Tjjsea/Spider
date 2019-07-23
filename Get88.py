import os
import re
import furl
import time
import json
import urllib
import requests
import multiprocessing as mp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.request import urlopen

def UrlOpen(url):
    req = urllib.request.Request(url)
    time.sleep(0.1)
    req.add_header('User-Agent',
                   'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36 LBBROWSER')
    response = urllib.request.urlopen(req)
    html = response.read()
    return html

def parsehphtml(url):
    '''
    解析首页，获取所有分类的链接
    '''
    html=UrlOpen(url)
    links=[]
    soup=BeautifulSoup(html,features='lxml')
    genres=soup.find('ul',{'class':'nav_l'})
    genrelinks=genres.find_all('a')[1:]
    for genre in genrelinks:
        links.append(urljoin(url,genre['href']))
    return links

def parsebookhtml1(url,starturl='https://www.88dush.com/'):
    '''
    解析分类小说页，获取当前分类所有小说的链接和对应的题目
    '''
    html=UrlOpen(url)
    soup=BeautifulSoup(html,features='lxml')
    books={}

    novellist=soup.find('div',{'class':'booklist'})
    novels=novellist.find_all('span',{'class':'sm'})[1:]
    for novel in novels:
        book=novel.find('a')
        title=book.find('b').get_text()
        if title in books:
            continue
        link=urljoin(starturl,book['href'])         
        books[title]=link               
    return books

def parsebookhtml2(url):
    '''
    解析分类小说页，获取该类别总页数返回所有分页的链接
    '''
    html=UrlOpen(url)
    soup=BeautifulSoup(html,features='lxml')
    allplinks=[]

    pagelinks=soup.find('div',{'class':'pagelink'})
    lastlink=pagelinks.find('a',{'class':'last'})
    lastnum=int(lastlink.get_text())
    return lastnum

def parsecataloguehtml(url,starturl='https://www.88dush.com/'):
    '''
    获取某本小说每一章的链接和类别
    '''
    html=UrlOpen(url)
    soup=BeautifulSoup(html,features='lxml')

    seclinks=[]
    sections=soup.find('div',{'class':'mulu'})
    sections=sections.find_all('a')
    for sec in sections:
        seclinks.append(urljoin(url,sec['href']))
    return seclinks

def parsenovelhtml(url):
    '''
    获取当前页面的小说内容
    返回包含标签和文本的字典
    '''
    html=UrlOpen(url)
    soup=BeautifulSoup(html,features='lxml')
    artical={}

    labels=['网络小说']
    label=soup.find('div',{'class':'read_t'})
    label=label.find_all('a')
    if len(label)>9:
        label=label[9]
    else:
        label=label[1]
    labels.append(label.get_text())

    novel=soup.find('div',{'class':'novel'})
    title=novel.find('h1').get_text()
    texts=title+'\n'
    contents=novel.find('div',{'class':'yd_text2'}).get_text()
    texts+=contents
    artical['labels']=labels
    artical['texts']=texts
    return artical

def savetitles(titles):
    with open('D:\\项目\\成语分级\\语料\\data\\titles.txt','w',encoding='utf-8') as fout:
        json.dump(list(titles),fout)
    
def savefailbooks(failbooks):
    with open('D:\\项目\\成语分级\\语料\\data\\failbooks.txt','w',encoding='utf-8') as fout:
        json.dump(list(failbooks),fout)
    
def downloadbook(pool,title,link,num=0):
    print('start get '+title+' '+link)
    t1=time.time()
    try:
        seclinks=parsecataloguehtml(link,homepage)
        articals=pool.map(parsenovelhtml,seclinks)
    except:
        if num<3:
            print('断开连接，尝试重连'+str(num))
            time.sleep(num*10)
            return downloadbook(pool,title,link,num+1)
        else:
            print('多次尝试，重连失败')
            return False
    else:
        file_path='D:\\项目\\成语分级\\语料\\novels\\'+title+'.json'
        with open(file_path,'w',encoding='utf-8') as fout:
            json.dump(articals,fout)
        t2=time.time()-t1
        print('Download '+title+' success with '+str(t2)+'s')
        return True

if __name__=='__main__':
    homepage='https://www.88dush.com/'
    booksurl='https://www.88dush.com/'

    pool=mp.Pool(50)

    files=os.listdir('D:\\项目\\成语分级\\语料\\novels')
    titles=[s.split('.')[0] for s in files]
    with open('D:\\项目\\成语分级\\语料\\data\\titles.txt','w',encoding='utf-8') as fout:
        json.dump(titles,fout)
    titles=set(titles)

    if os.path.exists('D:\\项目\\成语分级\\语料\\data\\failbooks.txt'):
        with open('D:\\项目\\成语分级\\语料\\data\\failbooks.txt',encoding='utf-8') as fin:
            failbooks=json.load(fin)
    else:
        failbooks=[]
    
    if os.path.exists('D:\\项目\\成语分级\\语料\\data\\bbbooks.json'):
        with open('D:\\项目\\成语分级\\语料\\data\\bbbooks.json',encoding='utf-8') as fin:
            books=json.load(fin)
    else:
        genrepagelinks=[] #所有类别的所有页面的链接
        genres=parsehphtml(homepage)   #所有分类页的首页
        for genre in genres:
            booknum=parsebookhtml2(genre) #某类别的页数
            templink=genre[:-2]
            genrepagelinks+=[templink+str(i) for i in range(1,booknum+1)] #某类别的所有页面的链接
        books={}
        for pagelink in genrepagelinks:
            books.update(parsebookhtml1(pagelink,homepage))
        with open('D:\\项目\\成语分级\\语料\\data\\bbbooks.json','w',encoding='utf-8') as fout:
            json.dump(books,fout)
    print('get all books')

    for title in books:
        if title in titles or title in failbooks:
            continue
        blink=books[title]
        if downloadbook(pool,title,blink):
            titles.add(title)
        else:
            failbooks.append(title)
            savefailbooks(failbooks)
    savetitles(titles)