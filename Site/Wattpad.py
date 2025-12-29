from random import randint
from typing import TYPE_CHECKING, List, Optional

import requests
from bs4 import BeautifulSoup, Tag

from Site import Common

if TYPE_CHECKING:
    from Site.Common import Progress


class Wattpad:
    title: str
    author: str
    story: str
    rawstoryhtml: List[Tag]
    length: int
    summary: str
    pbar: Optional["Progress"]
    url: str
    chapters: List[str]
    duplicate: bool

    def requestPage(self, url: str) -> Optional[requests.Response]:
        headerlist: List[str] = [
            "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/41.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        ]

        header: dict[str, str] = {
            "user-agent": headerlist[randint(0, len(headerlist) - 1)]
        }
        return Common.RequestPage(url, headers=header)

    def __init__(self, url: str) -> None:
        self.title = ""
        self.author = ""
        self.story = ""
        self.rawstoryhtml = []
        self.length = 1
        self.summary = ""
        self.pbar = None
        self.url = url
        self.chapters = []
        self.duplicate = False

        response = self.requestPage(self.url)
        if response is None or response.content is None:
            return

        soup = BeautifulSoup(response.content, "html.parser")
        title_h1 = soup.find("h1")
        if isinstance(title_h1, Tag):
            self.title = title_h1.get_text()

        if Common.dup:
            if Common.CheckDuplicate(self.title):
                self.duplicate = True
                return

        author_span = soup.find("span", attrs={"class": "author h6"})
        if isinstance(author_span, Tag):
            self.author = author_span.get_text()[3:]

        h2_tag = soup.find("h2")
        if isinstance(h2_tag, Tag):
            self.chapters.append(h2_tag.get_text())

        summary_p = soup.find("p", attrs={"class": "item-description"})
        if isinstance(summary_p, Tag):
            self.summary = summary_p.get_text()

        pre_tag = soup.find("pre")
        if isinstance(pre_tag, Tag):
            self.rawstoryhtml.append(pre_tag)

        Common.prnt(self.title + "\nby " + self.author + "\n" + self.summary)

        toc_ul = soup.find("ul", attrs={"class": "table-of-contents"})
        if isinstance(toc_ul, Tag):
            self.length = len(toc_ul.find_all("li"))

        self.pbar = Common.Progress(self.length)
        if self.pbar:
            self.pbar.Update()

        next_link = soup.find("a", attrs={"class": "next-part-link"})
        if isinstance(next_link, Tag):
            next_href = next_link.get("href")
            if isinstance(next_href, str):
                self.addNextPage(next_href)

        if self.pbar:
            self.pbar.End()

        for j in range(0, len(self.rawstoryhtml)):
            tmp = self.rawstoryhtml[j].prettify()[5:]
            tmp = tmp.replace("&amp;apos", "'")
            new_tag = BeautifulSoup(tmp, "html.parser").find()
            if isinstance(new_tag, Tag):
                self.rawstoryhtml[j] = new_tag

        for i in range(0, len(self.rawstoryhtml)):
            self.story = self.story + self.chapters[i] + "\n"
            self.story = self.story + self.rawstoryhtml[i].get_text()
        self.story = self.story.replace("\n", Common.lineEnding)

    def addNextPage(self, url: str) -> None:
        response = self.requestPage(url)
        if response is None or response.content is None:
            return

        soup = BeautifulSoup(response.content, "html.parser")
        h2_tag = soup.find("h2")
        if isinstance(h2_tag, Tag):
            self.chapters.append("Chapter " + h2_tag.get_text())

        pre_tag = soup.find("pre")
        if isinstance(pre_tag, Tag):
            self.rawstoryhtml.append(pre_tag)

        if self.pbar:
            self.pbar.Update()

        next_link = soup.find("a", attrs={"class": "next-part-link"})
        if isinstance(next_link, Tag):
            next_href = next_link.get("href")
            if isinstance(next_href, str):
                self.addNextPage(next_href)
