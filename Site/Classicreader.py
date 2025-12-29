import re
from typing import TYPE_CHECKING, List, Optional

import requests
from bs4 import BeautifulSoup, Tag

from Site import Common

if TYPE_CHECKING:
    from Site.Common import Progress


class Classicreader:
    title: str
    author: str
    story: str
    rawstoryhtml: List[Tag]
    chapters: List[str]
    pbar: Optional["Progress"]
    url: str
    duplicate: bool

    def requestPage(self, url: str) -> Optional[requests.Response]:
        return Common.RequestPage(url)

    def __init__(self, url: str) -> None:
        self.title = ""
        self.author = ""
        self.story = ""
        self.rawstoryhtml = []
        self.chapters = []
        self.pbar = None
        self.url = url
        self.duplicate = False
        page = self.requestPage(url)
        if page is None or page.content is None:
            print("Could not complete request for page: " + url)
            return

        soup = BeautifulSoup(page.content, "html.parser")
        # grabs important metadata information
        title_span = soup.find("span", attrs={"class": "book-header"})
        if isinstance(title_span, Tag):
            self.title = title_span.get_text()

        if Common.dup:
            if Common.CheckDuplicate(self.title):
                self.duplicate = True
                return

        Common.prnt(self.title)
        author_span = soup.find("span", attrs={"class": "by-line"})
        if isinstance(author_span, Tag) and len(author_span.contents) > 1:
            content = author_span.contents[1]
            if hasattr(content, "get_text"):
                self.author = content.get_text()  # type: ignore
        Common.prnt(self.author)

        # looks to see if on table of contents page
        if soup.find("h2") is None:
            categories_links = soup.find_all("a", attrs={"class": "categories"})
            # checks to see if single page story
            if len(categories_links) == 15:
                paragraphs = soup.find_all("p")
                text = ""
                for p in paragraphs:
                    p_text = re.sub(r"\n\s*", r"", p.get_text(), flags=re.M)
                    self.story += p_text + "\n\n"
                    text += "<p>" + p_text + "</p>\n"
                temp = BeautifulSoup(text, "html.parser")
                self.chapters.append(self.title)
                if isinstance(temp, Tag):
                    self.rawstoryhtml.append(temp)
                return
            try:
                toc_href = categories_links[7].get("href")
                if isinstance(toc_href, str):
                    url_toc = "https://www.classicreader.com" + toc_href
                    page_toc = requests.get(url_toc)
                    soup = BeautifulSoup(page_toc.content, "html.parser")
                    Common.prnt("got table of contents page")
            except Exception:
                paragraphs = soup.find_all("p")
                text = ""
                for p in paragraphs:
                    p_text = re.sub(r"\n\s*", r"", p.get_text(), flags=re.M)
                    self.story += p_text + "\n\n"
                    text += "<p>" + p_text + "</p>\n"
                temp = BeautifulSoup(text, "html.parser")
                self.chapters.append(self.title)
                if isinstance(temp, Tag):
                    self.rawstoryhtml.append(temp)
                return

        links = soup.find_all("a", attrs={"class": "chapter-title"})

        self.pbar = Common.Progress(len(links))

        for i in links:
            href = i.get("href")
            if isinstance(href, str):
                self.AddNextPage("https://www.classicreader.com" + href)
                self.chapters.append(i.get_text())
                if self.pbar:
                    self.pbar.Update()

        if self.pbar:
            self.pbar.End()

    def AddNextPage(self, link: str) -> None:
        page = self.requestPage(link)

        if page is None or page.content is None:
            print("Could not complete request for page: " + link)
            return

        soup = BeautifulSoup(page.content, "html.parser")
        paragraphs = soup.find_all("p")
        text = ""
        for p in paragraphs:
            p_text = re.sub(r"\n\s*", r"", p.get_text(), flags=re.M)
            self.story += p_text + "\n\n"
            text += "<p>" + p_text + "</p>\n"
        temp = BeautifulSoup(text, "html.parser")
        if isinstance(temp, Tag):
            self.rawstoryhtml.append(temp)
