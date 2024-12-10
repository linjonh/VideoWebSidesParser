import asyncio
from concurrent.futures import ThreadPoolExecutor
from ctypes import WinError
import time
from urllib import error, request

from bs4 import BeautifulSoup
import json as Json

BaseURL = "https://www.xiangguys.com"
loadMainExector = ThreadPoolExecutor(max_workers=12)
# datalPlayExector=ThreadPoolExecutor(max_workers=12)
# playurlExetor=ThreadPoolExecutor(max_workers=12)


def loadMain():
    # 首页
    # 获取导航栏地址
    soup = getSoup()
    allText = soup.select(".navbar a")
    allNaviHref = []
    for i in allText:
        # for s in i.stripped_strings:
        #     print(s)

        # print(i.prettify())
        a = i.attrs["href"]
        if a != "":
            allNaviHref.append(a)
            print("href=" + a)
    print(allNaviHref)
    futures = [
        loadMainExector.submit(parsePerpage(tab), f"Task-{tab}") for tab in allNaviHref
    ]
    allPlayUrls = []
    for future in futures:
        allPlayUrls.append(future.result)
    file = open("G:\\videoInfo.ini", "+w", encoding="utf-8")

    for i in range(0, len(allNaviHref)):
        tab = allNaviHref[i]
        tabM3u8Arrays = allPlayUrls[i]
        file.write(f"#{tab}\n")
        for m3u8 in tabM3u8Arrays:
            file.write(f"{m3u8}\n")
    file.close()
    # print(f"parse end! allPlayUrls={allPlayUrls}")
    print(f"parse end! ")
    return


def getSoup(url=BaseURL):
    try:
        start = time.time()

        header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        urlRequest = request.Request(url, headers=header)
        urlopen = request.urlopen(urlRequest)
        decode = urlopen.read().decode("utf-8")
        # print(decode)
        soup = BeautifulSoup(decode, "html.parser")
        # soup = BeautifulSoup(decode, "lxml")
        end = time.time()
        duration = end - start
        print(f"load time={duration}")
    except error.URLError as e:
        print(e)
        soup = retryGetSoup(url)
    except WinError as e:
        print(e)
        soup = retryGetSoup(url)

    return soup


def retryGetSoup(url):
    try:
        print(f"retry load url={url}")
        soup = getSoup(url)
    except error.URLError as e:
        print(e)
    return soup


class VideoItemInfo:
    def __init__(self, detailPageUrl, title, imageUrl, actors):
        self.detailPageUrl = detailPageUrl
        self.title = title
        self.imageUrl = imageUrl
        self.actors = actors


def parsePerpage(pageSeg, isNeedParsePageTag=True):
    # 切页解析
    # 获取分页信息和itemData
    url = BaseURL + pageSeg
    print(f"start parse:{url}")
    pageSoup = getSoup(url=url)
    listVideo = pageSoup.select(".thumbnail-group li")  # video list
    listPageItem = pageSoup.select(".page-link")  # page nav
    pageNavis = []
    videoItems = []
    allPlayUrls = []
    if isNeedParsePageTag:
        # page item parse
        if len(listPageItem) > 0:
            pageSize = listPageItem[-2]
            address = pageSize["href"]
            rindex = address.rindex("/")
            subStr = address[rindex + 1 :]
            subStrPre = address[: rindex + 1]
            print(subStr)
            count = subStr.replace("hjs", "").replace(".html", "")
            print(f"page count={count}")
            for i in range(1, int(count)):
                pageNavis.append(f"{subStrPre}hjs{i}.html")
                # print(el.prettify())
            print(f"pageNavis={pageNavis}")
    # vide item parse
    for el in listVideo:
        videoTag = el.select_one(".thumbnail")

        linkDetalPageUrl = videoTag.attrs["href"]  # 详情页地址
        title = videoTag.attrs["title"]  # 视频标题
        imageUrl = el.select_one("img").attrs["data-original"]  # 预览图
        actorsArray = el.select_one("p").stripped_strings  # 演员表
        actors = ""
        for s in actorsArray:
            actors += s + ","
        item = VideoItemInfo(linkDetalPageUrl, title, imageUrl, actors)
        # print(
        #     f"title={title} linkDetalPageUrl={linkDetalPageUrl} imageUrl={imageUrl} actorsArray={actors}"
        # )
        # print(item.__dict__)
        videoItems.append(item)
    # start to visit videoDetail:
    futures = [
        loadMainExector.submit(videoDetail(item.detailPageUrl), f"Task-{item.title}")
        for item in videoItems
    ]
    # print(visitDetailPageTasks.__dict__)
    datalPlayPages = []
    for future in futures:
        datalPlayPages.append(future.result)

    print(f"pageSeg={pageSeg} datas={datalPlayPages}")
    # start visit play page
    futures = [
        loadMainExector.submit(playVideoPage(link), f"Task-{item.title}")
        for link in datalPlayPages
    ]
    playUrls = []
    for future in futures:
        playUrls.append(future.result)
    print(f"pageSeg={pageSeg} playUrls={playUrls}")
    allPlayUrls.extend(playUrls)
    #   todo
    if len(pageNavis) > 0:
        for page in pageNavis:
            print(f"start parse next page:{page}")
            parsePerpage(page, False)
    return allPlayUrls


def videoDetail(pageSeg):
    # 获取到视频播放页地址

    url = BaseURL + pageSeg
    pageSoup = getSoup(url=url)
    #  print(pageSoup.prettify())
    detailPlay = pageSoup.select_one(".detail-play-list a")  # 播放高清视频按钮地址
    # print(detailPlay.prettify())
    linkUrl = detailPlay.attrs["href"]  # playVideoPage url address
    print(f"videoDetail={linkUrl}")
    return linkUrl


def playVideoPage(pageSeg):
    url = BaseURL + pageSeg
    pageSoup = getSoup(url=url)
    el = pageSoup.select_one(".player script")
    text = el.getText()
    l = text.index("=")
    r = text.index(";")
    json = text[l + 1 : r]
    obj = Json.loads(json)
    playUrl = obj["url"]
    print(f"pased playUrl={playUrl}")
    return playUrl  # m3u8 url


if __name__ == "__main__":
    print("hello")
    start = time.time()
    asyncio.run(loadMain())
    end = time.time()
    duration = end - start
    print(f"run duration time={duration}s , minus={duration/60}")
    # parsePerpage("/xiju/hjs1.html")
    # videoDetail("/video/3330.html")
    # playVideoPage("/video/play/3330-1-1.html")

    # item = VideoItemInfo("linkDetalPageUrl", "title", "imageUrl", "actors")
    # print(item.__dict__)
    # items = [item]
    # print(f"item:{[i.detailPageUrl for i in items]}")
