from random import randint
from typing import TYPE_CHECKING, List, Optional

import requests
from bs4 import BeautifulSoup, Tag

# TODO comments and cleaning up
from Site import Common

if TYPE_CHECKING:
    pass


class Literotica:
    title: str
    author: str
    story: str
    rawstoryhtml: List[Tag]
    storyhtml: str
    url: str
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
        self.storyhtml = ""
        self.url = url
        self.duplicate = False

        response = self.requestPage(self.url)
        if response is None or response.content is None:
            return

        soup = BeautifulSoup(response.content, "html.parser")
        titlehtml = soup.find("h1")
        if isinstance(titlehtml, Tag):
            self.title = titlehtml.text.strip()

        if Common.dup:
            if Common.CheckDuplicate(self.title):
                self.duplicate = True
                return

        authorhtml = soup.find("a", attrs={"class": "y_eU"})
        if isinstance(authorhtml, Tag):
            self.author = authorhtml.text.strip()

        story_div = soup.find("div", attrs={"class": "aa_ht"})
        if isinstance(story_div, Tag):
            self.rawstoryhtml.append(story_div)
            self.story = story_div.get_text(separator=Common.lineEnding)

        Common.prnt(self.title + " by " + self.author)

        nextLinkSoup = soup.find("a", attrs={"title": "Next Page"})
        if isinstance(nextLinkSoup, Tag):
            next_href = nextLinkSoup.get("href")
            if isinstance(next_href, str):
                self.AddNextPage(next_href)

        for i in self.rawstoryhtml:
            self.storyhtml += "".join(
                str(content.prettify()) if hasattr(content, "prettify") else str(content)
                for content in i.contents
            )

    def AddNextPage(self, thisLink: str) -> None:
        response = self.requestPage("https://www.literotica.com" + thisLink)
        if response is None or response.content is None:
            return

        soup = BeautifulSoup(response.content, "html.parser")

        story_div = soup.find("div", attrs={"class": "aa_ht"})
        if isinstance(story_div, Tag):
            self.rawstoryhtml.append(story_div)
            self.story += story_div.get_text(separator=Common.lineEnding)

        nextLinkSoup = soup.find("a", attrs={"title": "Next Page"})
        if isinstance(nextLinkSoup, Tag):
            next_href = nextLinkSoup.get("href")
            if isinstance(next_href, str):
                self.AddNextPage(next_href)
