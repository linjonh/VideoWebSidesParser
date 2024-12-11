import asyncio

# from ctypes import WinError
import os
import threading
import time
from urllib import error, request

from bs4 import BeautifulSoup
import json as Json

from MyLog import log

BaseURL = "https://www.xiangguys.com"
counterLock=threading.Lock()
countNum=0
dataFileDir="data"
def slice(array, isNeedSlice=False):
    if isNeedSlice:
        return array[:3]
    else:
        return array


def timeCost(func):
    def wrapper(*args, **argss):
        try:
            start = time.time()
            result = func(*args, **argss)
            end = time.time()
            duration = end - start
            log(f"load time={duration:.3f}")
        except Exception as e:
            log(e)
        return result

    return wrapper


@timeCost
def getSoup(url=BaseURL):
    try:
        header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        urlRequest = request.Request(url, headers=header)
        log("start urlRequest=" + url)
        urlopen = request.urlopen(urlRequest, timeout=5)
        decode = urlopen.read().decode("utf-8")
        soup = BeautifulSoup(decode, "html.parser")
        # soup = BeautifulSoup(decode, "lxml")
        log("end urlRequest=" + url)

    except Exception as e:
        log(e)
        # time.sleep(2)
        soup = retryGetSoup(url)
    return soup


def retryGetSoup(url):
    try:
        log(f"retry load url={url}")
        soup = getSoup(url)
    except Exception as e:
        log(e)
    return soup


class VideoItemInfo:
    def __init__(self, tab, detailPageUrl, title, imageUrl, m3u8="", actors=""):
        self.tab = tab
        self.detailPageUrl = detailPageUrl
        self.title = title
        self.imageUrl = imageUrl
        self.m3u8 = m3u8
        self.actors = actors


async def loadMain():
    # 首页
    # 获取导航栏地址
    soup = getSoup()
    allText = soup.select(".navbar a")
    allNaviHref: list[str] = []
    for i in allText:
        # for s in i.stripped_strings:
        #     log(s)

        # log(i.prettify())
        a = i.attrs["href"]
        if a != "":
            allNaviHref.append(a)
            log("href=" + a)
    log(allNaviHref)
    arr: list[list[list[VideoItemInfo]]] = [
        parsePerpage(tab) for tab in slice(allNaviHref)
    ]
    allVideoItems: list[list[VideoItemInfo]] = await asyncio.gather(*arr)

    os.makedirs(dataFileDir,exist_ok=True)
    await asyncio.gather(
        saveToJsonFile(allNaviHref, allVideoItems),
        saveToM3u8(allNaviHref, allVideoItems),
    )
    # log(f"parse end! allPlayUrls={allPlayUrls}")
    log(f"parse end! ")
    return


async def saveToJsonFile(allNaviHref, allVideoItems):
    json=""
    log("srart saveToJsonFile ")
    try:
        file = open(f"{dataFileDir}/videoInfo.json", "+w", encoding="utf-8")

        json: str = "{"

        for i in range(0, len(allVideoItems)):
            tab = allNaviHref[i].replace("/", "")
            if tab == "":
                tab = "home"
            tabVideItems: list[list[VideoItemInfo]] = allVideoItems[i]
            json += f' "{tab}":['
            for video in tabVideItems:
                json += f' {{ "title":"{video.title}","detailPageUrl":"{video.detailPageUrl}","imageUrl":"{video.imageUrl}","m3u8":"{video.m3u8}","actors":"{video.actors}" }},'
            json = json[:-1] + "],"

        json = json[:-1] + "}"
        # json = Json.loads(json)
        # pretifyed = Json.dumps(json, indent=4, ensure_ascii=False)
        file.write(json)
        file.close()
    except Exception as e:
        log(e)
        log(json)
        return False
    return True


async def saveToM3u8(allNaviHref, allVideoItems):
    log("srart saveToM3u8 ")

    try:
        for i in range(0, len(allVideoItems)):
            tab = allNaviHref[i].replace("/", "")
            if tab == "":
                tab = "home"
            fileName = f"{dataFileDir}/{tab}.m3u8"
            log(fileName)
            file = open(fileName, "+w", encoding="utf-8")
            file.write("#EXTM3U\n")

            tabVideItems = allVideoItems[i]
            for video in tabVideItems:
                logo = video.imageUrl
                file.write(
                    f'#EXTINF:-1 group-title="{tab}" tvg-logo="{logo}",{video.title}\n'
                )
                file.write(f"{video.m3u8}\n")
            file.close()
    except Exception as e:
        log(e)
        return False
    return True


async def parsePerpage(pageSeg, isNeedParsePageTag=True):
    # 切页解析
    # 获取分页信息和itemData
    url = BaseURL + pageSeg
    log(f"start parse:{url}")
    pageSoup = getSoup(url=url)
    listVideo = pageSoup.select(".thumbnail-group li")  # video list
    listPageItem = pageSoup.select(".page-link")  # page nav
    pageNavis = []
    videoItems = []
    if isNeedParsePageTag:
        # page item parse
        if len(listPageItem) > 0:
            pageSize = listPageItem[-2]
            address = pageSize["href"]
            rindex = address.rindex("/")
            subStr = address[rindex + 1 :]
            subStrPre = address[: rindex + 1]
            log(subStr)
            count = subStr.replace("hjs", "").replace(".html", "")
            log(f"page count={count}")
            for i in range(2, int(count)):
                pageNavis.append(f"{subStrPre}hjs{i}.html")
                # log(el.prettify())
            log(f"pageNavis={pageNavis[-1:]}")
    # vide item parse
    for el in slice(listVideo):
        videoTag = el.select_one(".thumbnail")

        linkDetalPageUrl = videoTag.attrs["href"]  # 详情页地址
        title = videoTag.attrs["title"]  # 视频标题
        imageUrl = el.select_one("img").attrs["data-original"]  # 预览图
        # actorsArray = el.select_one("p").stripped_strings  # 演员表
        # actors = ""
        # for s in actorsArray:
        #     actors += s + " | "
        item = VideoItemInfo(pageSeg, linkDetalPageUrl, title, imageUrl)
        # log(
        #     f"title={title} linkDetalPageUrl={linkDetalPageUrl} imageUrl={imageUrl} actorsArray={actors}"
        # )
        # log(item.__dict__)
        videoItems.append(item)
    # start to visit videoDetail:
    data = await asyncio.gather(*(videoDetail(item) for item in videoItems))

    # start visit play page
    playUrls = await asyncio.gather(
        *(playVideoPage(link, actorInfos) for (link, actorInfos) in data)
    )
    for i in range(0, len(playUrls)):
        item = videoItems[i]
        item.m3u8, item.actors = playUrls[i]
    log(f"pageSeg={pageSeg} playUrls.size={len(playUrls)}")
    #   todo
    if len(pageNavis) > 0:
        for page in pageNavis[:2]:
            log(f"start parse next page:{page}")
            nextPageItems = await parsePerpage(page, False)
            videoItems.extend(nextPageItems)
            log(
                f"next page videoSize={len(nextPageItems)} allAddedSize={len(videoItems)}"
            )

    return videoItems


async def videoDetail(item: VideoItemInfo):
    # 获取到视频播放页地址
    pageSeg = item.detailPageUrl
    url = BaseURL + pageSeg
    pageSoup = getSoup(url=url)
    #  log(pageSoup.prettify())
    detailPlay = pageSoup.select_one(".detail-play-list a")  # 播放高清视频按钮地址
    tag = pageSoup.select_one(".detail-actor")
    # log("detail-actor="+tag.prettify())
    detailActorInfos = tag.stripped_strings  # 详情

    # log(detailPlay.prettify())
    linkUrl = detailPlay.attrs["href"]  # playVideoPage url address
    log(f"tab={item.tab} videoDetail={linkUrl}")
    return (linkUrl, detailActorInfos)


async def playVideoPage(pageSeg, actorInfos:list[str]):
    url = BaseURL + pageSeg
    pageSoup = getSoup(url=url)
    el = pageSoup.select_one(".player script")
    text = el.getText()
    l = text.index("=")
    r = text.index(";")
    json = text[l + 1 : r]
    obj = Json.loads(json)
    playUrl = obj["url"]
    log(f"pased playUrl={playUrl}")

    detailInfo = ""
    for i in actorInfos:              
        detailInfo += "|" + i.strip().strip("\n").replace("\n", "").replace("\"","“").replace("\t","")
    counterLock.acquire()
    global countNum
    countNum+=1
    log(f"countNum={countNum:<6} pageSeg={pageSeg} actorInfos={type(actorInfos)} detailInfo={detailInfo[:20]}")
    counterLock.release()
    return (playUrl, detailInfo)  # m3u8 url


if __name__ == "__main__":
    log("hello")
    start = time.time()
    asyncio.run(loadMain())
    end = time.time()
    log(f"run duration time={(end-start):.3f}")
    # parsePerpage("/xiju/hjs1.html")
    # videoDetail("/video/3330.html")
    # playVideoPage("/video/play/3330-1-1.html")

    # item = VideoItemInfo("linkDetalPageUrl", "title", "imageUrl", "actors")
    # log(item.__dict__)
    # items = [item]
    # log(f"item:{[i.detailPageUrl for i in items]}")
