import queue
import threading
from typing import TYPE_CHECKING, Any, List, Optional

import requests
from bs4 import BeautifulSoup, Tag

from Site import Common

if TYPE_CHECKING:
    from Site.Common import Progress


class Nhentai:
    title: str
    chapters: List[str]
    author: str
    story: str
    temp: List[Any]
    rawstoryhtml: List[Tag]
    truestoryhttml: List[str]
    length: int
    pbar: Optional["Progress"]
    url: str
    images: List[str]
    hasimages: bool
    isize: int
    duplicate: bool
    queue: queue.Queue[Any]

    def requestPage(self, url: str) -> Optional[requests.Response]:
        return Common.RequestPage(url)

    def __init__(self, url: str) -> None:
        self.title = ""
        self.chapters = [""]
        self.author = ""
        self.story = ""
        self.temp = []
        self.rawstoryhtml = []
        self.truestoryhttml = []
        self.length = 1
        self.pbar = None
        self.url = url
        self.images = []
        self.hasimages = True
        self.isize = 0
        self.duplicate = False
        self.queue = queue.Queue()

        page = self.requestPage(url)

        if page is None or page.content is None:
            print("Could not complete request for page: " + url)
            return

        soup = BeautifulSoup(page.content, "html.parser")
        meta_name = soup.find("meta", attrs={"itemprop": "name"})
        if isinstance(meta_name, Tag):
            content = meta_name.get("content")
            if isinstance(content, str):
                self.title = content

        if Common.dup:
            if Common.CheckDuplicate(self.title):
                self.duplicate = True
                return

        for au in soup.find_all("div", attrs={"class": "tag-container"}):
            if isinstance(au, Tag):
                for au2 in au.find_all("a"):
                    href = au2.get("href")
                    if isinstance(href, str) and href[:7] == "/artist":
                        self.author = href[8:-1]
        Common.prnt(self.title + " by " + self.author)

        self.truestoryhttml.append("")
        self.isize = len(soup.find_all("a", attrs={"rel": "nofollow"}))

        if Common.opf is not None and any(
            x in ("html", "HTML", "txt", "TXT") for x in Common.opf
        ):
            self.pbar = Common.Progress(self.isize)

        for i in soup.find_all("a", attrs={"rel": "nofollow"}):
            href = i.get("href")
            if isinstance(href, str):
                self.GetURLS(href)
                break
        self.AddPage()

        if (
            Common.opf is not None
            and any(x in ("txt", "html", "TXT", "HTML") for x in Common.opf)
            and Common.mt
        ):
            for _ in range(0, len(self.images)):
                self.queue.get()

        if self.pbar is not None:
            self.pbar.End()

        # Adhere to SiteProvider protocol
        for html_content in self.truestoryhttml:
            self.rawstoryhtml.append(BeautifulSoup(html_content, "html.parser"))

    def GetURLS(self, url: str) -> None:
        page = self.requestPage("https://nhentai.net" + url.rstrip())

        if page is None or page.content is None:
            print("Could not complete request for page: " + url)
            return

        soup = BeautifulSoup(page.content, "html.parser")
        thisimage: str = ""
        try:
            image_container = soup.find("section", attrs={"id": "image-container"})
            if isinstance(image_container, Tag):
                img_tag = image_container.find("img")
                if isinstance(img_tag, Tag):
                    src = img_tag.get("src")
                    if isinstance(src, str):
                        thisimage = src
                        self.images.append(thisimage)
        except Exception:
            print("Error in: " + url)

        if thisimage:
            for i in range(2, self.isize + 1):
                self.images.append(thisimage[:-5] + str(i) + thisimage[-4:])

    def AddPage(self) -> None:
        i = 1
        for thisimage in self.images:
            if Common.opf is not None and any(
                x in ("html", "HTML", "epub", "EPUB") for x in Common.opf
            ):
                zeros = "0" * (len(str(self.isize)) - 1)
                num = i
                if len(zeros) > 1 and num > 9:
                    zeros = "0"
                elif len(zeros) == 1 and num > 9:
                    zeros = ""
                if num > 99:
                    zeros = ""
                self.truestoryhttml[0] = (
                    self.truestoryhttml[0]
                    + '<p><img src="'
                    + zeros
                    + str(num)
                    + '.jpg" /></p>\n'
                )
            if Common.opf is not None and any(
                x in ("html", "HTML", "txt", "TXT") for x in Common.opf
            ):
                if Common.mt:
                    t = threading.Thread(
                        target=Common.imageDL,
                        args=(
                            self.title,
                            thisimage,
                            i,
                            self.isize,
                            self.pbar,
                            self.queue,
                        ),
                        daemon=False,
                    )
                    t.start()
                else:
                    Common.imageDL(self.title, thisimage, i, self.isize, self.pbar)
            i += 1
