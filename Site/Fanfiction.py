import re
import urllib.parse
from typing import TYPE_CHECKING, List, Optional

import requests
from bs4 import BeautifulSoup, Tag

from Site import Common

if TYPE_CHECKING:
    from Site.Common import Progress


# TODO clean up and comment
class Fanfiction:
    title: str
    author: str
    story: str
    rawstoryhtml: List[Tag]
    storyhtml: str
    chapters: List[str]
    summary: str
    pbar: Optional["Progress"]
    url: str
    duplicate: bool

    def requestPage(self, url: str) -> Optional[requests.Response]:
        return Common.RequestPage(url)

    def __init__(self, url: str) -> None:
        # simple string for the title
        self.title = ""
        # simple string for the author
        self.author = ""
        # Extra long string containing the text of the story
        self.story = ""
        # each node of the list contains the raw html for one page of the story
        self.rawstoryhtml = []
        # the raw html but prettified and concatenated together
        self.storyhtml = ""
        # array of chapter names
        self.chapters = []
        # summary
        self.summary = ""
        self.pbar = None
        self.url = url
        self.duplicate = False

        page = self.requestPage(url)

        if page is None or page.content is None:
            print("Could not complete request for page: " + url)
            return

        soup = BeautifulSoup(page.content, "html.parser")
        story_div = soup.find("div", attrs={"id": "storytext"})
        if isinstance(story_div, Tag):
            self.rawstoryhtml.append(story_div)

        # Fucking magic that collects the chapter titles
        # probably doesn't work for all stories
        # seems to work for all stories, adds extra chapter title to end, oh well
        try:
            chap_select = soup.find(attrs={"id": "chap_select"})
            if isinstance(chap_select, Tag):
                for child in chap_select.descendants:
                    if not hasattr(child, "string") or child.string is None:
                        continue
                    else:
                        self.chapters.append(str(child.string))
                # we end up with an extra chapter at the end of the file, so the band-aid fix is to delete the last node
                if len(self.chapters) > 0:
                    del self.chapters[len(self.chapters) - 1]
        except Exception:
            print("Chapter name couldn't be grabbed")
            b_tag = soup.find("b", attrs={"class": "xcontrast_txt"})
            if isinstance(b_tag, Tag):
                self.chapters.append(b_tag.text.strip())

        """So here's the deal. fanfiction.net doesn't close any of the <option> tags that contain the chapter names, so BeautifulSoup closes them all
            at the end. This means that each option is the child of the option above it. so good luck extracting the name of each chapter individually
            There's also two (2) chapter selection fields on each web page, which makes the output look worse than it really is, since we're only ever
            going to use the first one we won't have to worry about it
            """
        # print("Chapters:")
        # print(self.chapters)
        summary_divs = soup.find_all("div", attrs={"class": "xcontrast_txt"})
        if summary_divs:
            self.summary = summary_divs[0].text.strip()

        author_links = soup.find_all("a", attrs={"class": "xcontrast_txt"})
        if len(author_links) > 2:
            self.author = author_links[2].text.strip()

        title_b = soup.find("b", attrs={"class": "xcontrast_txt"})
        if isinstance(title_b, Tag):
            self.title = title_b.text.strip()

        if Common.dup:
            if Common.CheckDuplicate(self.title):
                self.duplicate = True
                return

        Common.prnt(self.title + "\nby " + self.author + "\n" + self.summary)

        # setup progress bar

        # exception handling to avoid errors on single page stories
        prev_button = soup.find("button", attrs={"type": "BUTTON"})
        if isinstance(prev_button, Tag) and prev_button.text.strip() == "< Prev":
            print(
                "Non-first page entered. Ebook-Publisher will only add subsequent pages and chapter titles will be wrong"
            )
        for i in soup.find_all("button", attrs={"type": "BUTTON"}):
            if i.text.strip() == "Next >":
                self.pbar = Common.Progress(len(self.chapters))
                if self.pbar:
                    self.pbar.Update()
                self.AddNextPage(soup)
                break

        if self.pbar:
            self.pbar.End()

        for i in self.rawstoryhtml:
            for j in i.contents:
                if isinstance(j, Tag):
                    self.storyhtml += j.get_text() + "\n\n"
                else:
                    self.storyhtml += str(j)
        # print(self.storyhtml)
        self.story = self.storyhtml
        self.story = BeautifulSoup(self.story, "html.parser").text
        self.story = re.sub(r"\n\s*\n", r"\n\n", self.story, flags=re.M)
        # print(self.chapters)

    def AddNextPage(self, soup: BeautifulSoup) -> None:
        for i in soup.find_all("button"):
            if i.text.strip() == "Next >":
                rawnexturl = i.get("onclick")
                if not isinstance(rawnexturl, str):
                    continue

                if urllib.parse.urlparse(self.url)[1] == "www.fanfiction.net":
                    nexturl = "https://www.fanfiction.net" + rawnexturl[15:-1]
                else:
                    nexturl = "https://www.fictionpress.com" + rawnexturl[15:-1]
                # print(nexturl)
                page = self.requestPage(nexturl)

                if page is None or page.content is None:
                    print("Could not complete request for page: " + nexturl)
                    return

                soup = BeautifulSoup(page.content, "html.parser")
                story_div = soup.find("div", attrs={"id": "storytext"})
                if isinstance(story_div, Tag):
                    self.rawstoryhtml.append(story_div)
                if self.pbar:
                    self.pbar.Update()
                self.AddNextPage(soup)
                break
