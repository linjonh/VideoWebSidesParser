from ctypes import WinError
import string
from urllib import request
import urllib.error
from flask import Flask, redirect, render_template
import urllib
from bs4 import BeautifulSoup

from MyLog import log

app = Flask(__name__)
app.debug = False

baseUrl = "https://www.xiangguys.com"
subfix = "hjs1.html"
urlFormat = baseUrl + "{tab}" + subfix
urlDetail = baseUrl + "/video/" + "{tab}"


@app.route("/")
def home():
    # parse the home page menu

    # dataListTagHtml: string = ""
    # for i in range(0, 10):
    #     dataListTagHtml += f"<li>电影item{i}</li>\n"
    dataListTagHtml = parsePage(tab="juqing")
    return render_template("index.html", dataListTag=dataListTagHtml)


@app.route("/page/<tab>/")
def navigateToPage(tab):
    dataListTagHtml = parsePage(tab=tab)
    return render_template("index.html", dataListTag=dataListTagHtml)


@app.route("/video/<page>")
def videoDetail(page):
    dataListTagHtml = parsePage(tab=page, isDetal=True)
    return render_template("video.html", dataListTag=dataListTagHtml)


@app.route("/video/play/<page>")
def play_video(page):
    # launch dplayer html to play m3u8 video
    url = baseUrl + f"/video/play/{page}"
    video_url = parseVideoPlayUrl(url)  # [1:-1]
    # video_url = parseVideoPlayUrl(url)[1:-1]
    log(f"play video:{video_url}")
    # return redirect(f"https://www.dplayer.top/index.php?url={video_url}")
    return render_template("player.html", video_url=video_url)


#                         <li id="nav-dongzuo"><a href="/dongzuo/">动作片</a></li>
#                         <li id="nav-xiju"><a href="/xiju/">喜剧片</a></li>
#                         <li id="nav-aiqing"><a href="/aiqing/">爱情片</a></li>
#                         <li id="nav-kehuan"><a href="/kehuan/">科幻片</a></li>
#                         <li id="nav-kongbu"><a href="/kongbu/">恐怖片</a></li>
#                         <li id="nav-juqing"><a href="/juqing/">剧情片</a></li>
#                         <li id="nav-zhanzheng"><a href="/zhanzheng/">战争片</a></li>
#                         <li id="nav-donghua"><a href="/donghua/">动漫片</a></li>
def parsePage(tab: string, isDetal=False):
    if tab == "":
        url = baseUrl
    elif isDetal:
        url = urlDetail.format(tab=tab)
    else:
        url = urlFormat.format(tab="/" + tab + "/")
    log(f"start open url={url}")
    html = ""
    try:
        soup = getDocumentSoup(url)
        if isDetal:
            html = soup.find("div", class_="detail clearfix")
        else:
            html = soup.find("div", class_="content")
        # log(html.prettify())
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)
    except WinError as e:
        print(e)

    return html


def getDocumentSoup(url):
    soup = ""
    try:
        head = {  # 模拟浏览器头部信息，向服务器发送消息
            "User-Agent": "Mozilla / 5.0(Windows NT 10.0; Win64; x64) AppleWebKit / 537.36(KHTML, like Gecko) Chrome / 80.0.3987.122  Safari / 537.36"
        }
        # 用户代理，表示告诉服务器，我们是什么类型的机器、浏览器（本质上是告诉浏览器，我们可以接收什么水平的文件内容）
        Request = request.Request(url, headers=head)
        res = request.urlopen(Request)
        # get document
        document = res.read().decode("utf-8")
        soup = BeautifulSoup(document, "html.parser")
        # log(soup.title.text)
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)
    except WinError as e:
        print(e)
    return soup


def parseVideoPlayUrl(url):
    # 解析地址
    # page="3424-1-1.html"
    # url=baseUrl+f"/video/play/{page}"
    soup = getDocumentSoup(url)
    js = soup.find("div", class_="player").script.text
    if js != None:
        key = '"url":'
        left = js.index(key)
        js = js[left + len(key) :]
        right = js.index(",")
        playUrl = js[:right]
    else:
        return ""
    playUrl = playUrl.encode("utf-8").decode("unicode_escape").replace("\\","")
    log(playUrl)

    return playUrl


if __name__ == "__main__":
    app.run()
