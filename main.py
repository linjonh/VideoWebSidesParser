import asyncio

# from ctypes import WinError
import time
from urllib import error, request

from bs4 import BeautifulSoup
import json as Json

BaseURL = "https://www.xiangguys.com"


def slice(array, isNeedSlice=False):
    if isNeedSlice:
        return array[1:2]
    else:
        return array


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
    except Exception as e:
        print(e)
        soup = retryGetSoup(url)
    return soup


def retryGetSoup(url):
    try:
        print(f"retry load url={url}")
        soup = getSoup(url)
    except Exception as e:
        print(e)
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
        #     print(s)

        # print(i.prettify())
        a = i.attrs["href"]
        if a != "":
            allNaviHref.append(a)
            print("href=" + a)
    print(allNaviHref)
    arr: list[list[list[VideoItemInfo]]] = [
        parsePerpage(tab) for tab in slice(allNaviHref)
    ]
    allVideoItems: list[list[VideoItemInfo]] = await asyncio.gather(*arr)

    await asyncio.gather(saveToJsonFile(), saveToM3u8(allNaviHref, allVideoItems))
    # print(f"parse end! allPlayUrls={allPlayUrls}")
    print(f"parse end! ")
    return


async def saveToJsonFile(allNaviHref, allVideoItems):
    try:
        file = open("./videoInfo.ini", "+w", encoding="utf-8")

        json: str = "{{"

        for i in range(0, len(allVideoItems)):
            tab = allNaviHref[i]
            if tab == "":
                tab = "home"
            tabVideItems: list[list[VideoItemInfo]] = allVideoItems[i]
            json += f' "{tab}"=['
            for video in tabVideItems:
                json += f' {{ "title"="{video.title}","imageUrl"="{video.imageUrl}","m3u8\="{video.m3u8}","actors"="{video.actors}" }} ,'

            json = json[:-1] + "]"
        json += "}}"
        pretifyed = Json.dumps(json, indent=4)
        file.write(pretifyed)
        file.close()
    except Exception as e:
        print(e)
        return False
    return True


async def saveToM3u8(allNaviHref, allVideoItems):
    try:
        for i in range(0, len(allVideoItems)):
            tab = allNaviHref[i].replace("/", "")
            if tab == "":
                tab = "home"
            fileName = f"./{tab}.m3u8"
            print(fileName)
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
        print(e)
        return False
    return True


async def parsePerpage(pageSeg, isNeedParsePageTag=True):
    # 切页解析
    # 获取分页信息和itemData
    url = BaseURL + pageSeg
    print(f"start parse:{url}")
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
            print(subStr)
            count = subStr.replace("hjs", "").replace(".html", "")
            print(f"page count={count}")
            for i in range(2, int(count)):
                pageNavis.append(f"{subStrPre}hjs{i}.html")
                # print(el.prettify())
            print(f"pageNavis={pageNavis[-1:]}")
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
        # print(
        #     f"title={title} linkDetalPageUrl={linkDetalPageUrl} imageUrl={imageUrl} actorsArray={actors}"
        # )
        # print(item.__dict__)
        videoItems.append(item)
    # start to visit videoDetail:
    data = await asyncio.gather(*(videoDetail(item) for item in slice(videoItems)))
    detailInfo = ""
    for link, infos in data:
        for i in infos:
            detailInfo = detailInfo + " | " + i
    print(f"pageSeg={pageSeg} datalPlaySize={len(data)}")
    # start visit play page
    playUrls = await asyncio.gather(*(playVideoPage(link) for (link, infos) in data))
    for i in range(0, len(playUrls)):
        item = videoItems[i]
        item.m3u8 = playUrls[i]
        item.actors = detailInfo
    print(f"pageSeg={pageSeg} playUrls.size={len(playUrls)}")
    #   todo
    if len(pageNavis) > 0:
        for page in pageNavis[:2]:
            print(f"start parse next page:{page}")
            nextPageItems = await parsePerpage(page, False)
            videoItems.extend(nextPageItems)
            print(
                f"next page videoSize={len(nextPageItems)} allAddedSize={len(videoItems)}"
            )

    return videoItems


async def videoDetail(item: VideoItemInfo):
    # 获取到视频播放页地址
    pageSeg = item.detailPageUrl
    url = BaseURL + pageSeg
    pageSoup = getSoup(url=url)
    #  print(pageSoup.prettify())
    detailPlay = pageSoup.select_one(".detail-play-list a")  # 播放高清视频按钮地址
    detailInfos = pageSoup.select_one(".detail-actor").stripped_strings  # 详情

    # print(detailPlay.prettify())
    linkUrl = detailPlay.attrs["href"]  # playVideoPage url address
    print(f"tab={item.tab} videoDetail={linkUrl}")
    return (linkUrl, detailInfos)


async def playVideoPage(pageSeg):
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
    print(f"run duration time={(end-start):.2f}")
    # parsePerpage("/xiju/hjs1.html")
    # videoDetail("/video/3330.html")
    # playVideoPage("/video/play/3330-1-1.html")

    # item = VideoItemInfo("linkDetalPageUrl", "title", "imageUrl", "actors")
    # print(item.__dict__)
    # items = [item]
    # print(f"item:{[i.detailPageUrl for i in items]}")
