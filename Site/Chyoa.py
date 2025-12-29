import queue
import threading
import urllib.parse
from datetime import datetime
from threading import Lock
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from Site import Common

if TYPE_CHECKING:
    from Site.Common import Progress

lock: Lock = Lock()
lock2: Lock = Lock()


class Chyoa:
    title: str
    author: str
    authors: List[str]
    chapters: List[str]
    story: str
    temp: List[str]
    epubtemp: List[str]
    rawstoryhtml: List[Tag]
    epubrawstoryhtml: List[Tag]
    questions: List[str]
    summary: str
    renames: List[str]
    oldnames: List[str]
    truestoryhttml: List[str]
    epubtruestoryhttml: List[str]
    length: int
    pbar: Optional["Progress"]
    url: str
    images: List[str]
    hasimages: bool
    duplicate: bool
    backwards: bool
    depth: List[str]
    quiet: bool
    epubnextpages: List[str]
    nextLinks: List[str]
    partial: bool
    partialStart: int
    ogUrl: str
    pageIDs: List[int]
    pageIDIter: int
    pageIDDict: Dict[str, int]
    q: queue.Queue[Any]
    pageQueue: List[Any]
    Pages: List[Any]

    def requestPage(self, url: str) -> Optional[Any]:
        return Common.RequestPageChyoa(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}
        )

    def __init__(self, url: str) -> None:
        self.title = ""
        # initial author only for title page
        self.author = ""
        # author for each individual chapter
        self.authors = []
        # the h1 tag
        self.chapters = []
        self.story = ""
        self.temp = []
        self.epubtemp = []
        self.rawstoryhtml = []
        self.epubrawstoryhtml = []
        # the question at the end of each page
        self.questions = []
        self.summary = ""
        self.renames = []
        self.oldnames = []
        self.truestoryhttml = []
        self.epubtruestoryhttml = []
        self.length = 1
        self.pbar = None
        self.url = url
        self.images = []  # testing images
        self.hasimages = False
        self.duplicate = False
        self.backwards = not Common.chyoa_force_forwards
        self.depth = []
        self.quiet = Common.quiet
        self.epubnextpages = []
        self.nextLinks = []
        self.partial = False
        self.partialStart = 1
        self.ogUrl = self.url
        self.pageIDs = []
        self.pageIDIter = 0
        self.pageIDDict = {}
        self.q = queue.Queue()
        self.pageQueue = []
        self.Pages = []

        page = self.requestPage(url)

        if page is None:
            print("Could not complete request for page: " + url)
            return

        soup = BeautifulSoup(page.content, "html.parser")
        h3_tag = soup.find("h3")
        h1_tag = soup.find("h1")

        if h3_tag is None:
            if isinstance(h1_tag, Tag):
                self.title = h1_tag.get_text()
            self.backwards = False
        else:
            self.title = h3_tag.get_text()
            if self.title == "Log In":
                try:
                    if isinstance(h1_tag, Tag):
                        self.title = h1_tag.get_text()
                    self.backwards = False
                except Exception:
                    pass
            elif not self.backwards:
                self.partial = True

        # get update timestamp:
        if (self.backwards or not self.partial) and Common.chyoaDupCheck:
            dates_p = soup.find("p", attrs={"class": "dates"})
            if isinstance(dates_p, Tag) and dates_p.strong:
                date = dates_p.strong.get_text()
                # date='Jun 18, 2022'
                timestamp = datetime.strptime(date, "%b %d, %Y")
                # print(timestamp)
                if not Common.CheckDuplicateTime(self.title, timestamp):
                    Common.prnt("Story not updated: " + self.url, f=True)
                    self.duplicate = True
                    return

        # check duplicate with timestamp

        if Common.dup:
            if Common.CheckDuplicate(self.title):
                self.duplicate = True
                return

        meta_p = soup.find("p", class_="meta")
        if isinstance(meta_p, Tag):
            meta_a = meta_p.find("a")
            if isinstance(meta_a, Tag):
                self.authors.insert(0, meta_a.get_text())

            tmp = meta_p.get_text()
            t = [s for s in tmp.split() if s.isdigit()]
            if t:
                self.length = int(t[0])
                self.partialStart = self.length

        if isinstance(h1_tag, Tag):
            self.chapters.insert(0, h1_tag.get_text())

        synopsis_p = soup.find("p", attrs={"class": "synopsis"})
        if isinstance(synopsis_p, Tag):
            self.summary = synopsis_p.get_text()

        immersion_form = soup.find("form", attrs={"id": "immersion-form"})
        if isinstance(immersion_form, Tag):
            inputs = immersion_form.find_all("input", attrs={"value": ""})
            with lock:
                if Common.mt:
                    Common.quiet = True
                for i in range(len(inputs)):
                    print(self.title)
                    label = soup.find("label", attrs={"for": "c" + str(i)})
                    label_text = label.get_text() if isinstance(label, Tag) else ""
                    placeholder = inputs[i].get("placeholder")
                    if isinstance(placeholder, list):
                        placeholder = " ".join(placeholder)
                    elif not isinstance(placeholder, str):
                        placeholder = ""
                    print(
                        "Input immersion variable "
                        + str(i)
                        + " "
                        + label_text
                        + " ("
                        + placeholder
                        + ") (Leave blank to keep placeholder name)"
                    )
                    try:
                        newname = input()
                        self.renames.append(newname)
                    except Exception:
                        self.renames.append("")
                    self.oldnames.append(placeholder)
                    if self.renames[i] == "":
                        self.renames[i] = self.oldnames[i]
            if Common.mt:
                Common.quiet = self.quiet

        Common.prnt(self.title + "\n" + str(self.authors) + "\n" + self.summary)

        if self.backwards:
            self.pbar = Common.Progress(self.length)

        if Common.images:
            content_div = soup.find("div", attrs={"class": "chapter-content"})
            if isinstance(content_div, Tag) and content_div.find("img"):
                with lock2:
                    for simg in content_div.find_all("img"):
                        imgtemp = simg.get("src")
                        if isinstance(imgtemp, str):
                            simg["src"] = (
                                "img" + str(len(Common.urlDict[self.ogUrl]) + 1) + ".jpg"
                            )
                            Common.urlDict[self.ogUrl][
                                len(Common.urlDict[self.ogUrl])
                            ] = imgtemp
                self.hasimages = True

        content_div = soup.find("div", attrs={"class": "chapter-content"})
        temp = str(content_div) if isinstance(content_div, Tag) else ""

        # The second H2 tag may not exist if there is no sub title on a story, so we grab the first in such an event
        try:
            q_header = soup.find("header", attrs={"class": "question-header"})
            if isinstance(q_header, Tag):
                self.questions.insert(0, q_header.get_text())
            else:
                h2_tags = soup.find_all("h2")
                if h2_tags:
                    self.questions.insert(0, h2_tags[0].get_text())
        except IndexError:
            h2_tags = soup.find_all("h2")
            if h2_tags:
                self.questions.insert(0, h2_tags[0].get_text())

        if self.questions:
            temp += "<h2>" + self.questions[0] + "</h2>"
        self.temp.insert(0, temp)
        if self.backwards and self.pbar:
            self.pbar.Update()

        for a_tag in soup.find_all("a"):
            if a_tag.text.strip() == "Previous Chapter" and self.backwards:
                newLink = a_tag.get("href")
                while isinstance(newLink, str):
                    newLink = self.AddPrevPage(newLink)

                self.backwards = True
                break

        # Gets here if it's the intro page that is used
        if not self.backwards:
            self.Pages = []
            urls = []

            # Starting the Progress Bar
            numChaptersStr = "0"
            numChaptersTempTemp = soup.find_all("li")
            for li_tag in numChaptersTempTemp:
                if li_tag.find("i", attrs={"class": "bt-book-open"}):
                    numChaptersStr = li_tag.get_text().split()[0]
                    # Removes commas from stories with over 999 pages
                    numChaptersStr = numChaptersStr.replace(",", "")

            numChaptersInt = int(numChaptersStr)
            try:
                if not Common.mt:
                    if self.partial:
                        print("Downloading an unknown number of pages")
                    else:
                        self.pbar = Common.Progress(numChaptersInt)
                        if self.pbar:
                            self.pbar.Update()
            except Exception:
                pass

            j = 1
            self.temp[0] += "\n<br />"
            self.epubtemp = self.temp.copy()
            q_content = soup.find("div", attrs={"class": "question-content"})
            if isinstance(q_content, Tag):
                for a_tag in q_content.find_all("a"):
                    link = a_tag.get_text()
                    if link.strip() != "Add a new chapter":
                        # Band aid fix for replaceable text in the next chapter links

                        for i_rename in range(len(self.renames)):
                            link = link.replace(self.oldnames[i_rename], self.renames[i_rename])

                        if Common.opf is not None and any(
                            x in ("epub", "EPUB") for x in Common.opf
                        ):
                            self.epubtemp[0] += (
                                '\n<a href="'
                                + str(j)
                                + '.xhtml">'
                                + link.strip()
                                + "</a>\n<br />"
                            )

                        nextLink = (
                            '\n<a href="#'
                            + str(j)
                            + '">'
                            + "Previous Chapter"
                            + "</a>\n<br />"
                        )
                        self.temp[0] += (
                            '\n<a href="#' + str(j) + '">'
                            + link.strip()
                            + "</a>\n<br />"
                        )
                        self.nextLinks.append(nextLink)
                        href = a_tag.get("href")
                        if isinstance(href, str):
                            urls.append(href)
                        j += 1
            self.Pages.extend(urls)
            j = 1
            self.pageQueue = []
            for u in urls:
                if Common.mt and not self.partial:
                    chapNum = 0
                    if isinstance(meta_p, Tag):
                        meta_text = meta_p.get_text().split()
                        if len(meta_text) > 1:
                            chapNum = int(meta_text[1])
                    firstLinkId = None
                    threading.Thread(
                        target=self.ThreadAdd,
                        args=(
                            u,
                            j,
                            self.renames,
                            self.oldnames,
                            chapNum,
                            '<a href="#Chapter 0">Previous Chapter</a>\n<br />',
                            '\n<a href="'
                            + "Chapter 1"
                            + '.xhtml">'
                            + "Previous Chapter"
                            + "</a>\n<br />",
                            self.nextLinks[j - 1],
                            firstLinkId,
                            self.url,
                        ),
                        daemon=True,
                    ).start()  # TODO
                else:
                    if Common.mt:
                        Common.prnt(
                            "Warning: Cannot multithread partial Chyoa story: "
                            + self.url
                            + "\nUsing default method to download an unknown number of pages"
                        )
                    defArgs = (
                        u,
                        str(j),
                        1,
                        '<a href="#Chapter 0">Previous Chapter</a>\n<br />',
                        '\n<a href="'
                        + "Chapter 1"
                        + '.xhtml">'
                        + "Previous Chapter"
                        + "</a>\n<br />",
                        self.nextLinks[j - 1],
                        None,
                    )
                    self.pageQueue.append(defArgs)
                    while self.pageQueue:
                        self.AddNextPage(self.pageQueue.pop(0))

                j += 1
            if Common.mt and not self.partial:
                i_rem = numChaptersInt - 1
                print("Pages to add: " + str(i_rem))
                while i_rem > 0:
                    try:
                        self.q.get(timeout=30)
                    except queue.Empty:
                        print(
                            "Unsure if all threads ended. Expected reamining pages: "
                            + str(i_rem)
                        )
                        break
                    i_rem -= 1
                # print(threading.active_count())
                self.pageQueue = []

                for pg in self.Pages:
                    self.pageQueue.append(pg)
                    while self.pageQueue:
                        self.addPage(self.pageQueue.pop(0))
            # print(self.pageIDDict)
            for p in range(len(self.epubtemp)):
                for d in self.depth:
                    if (self.epubtemp[p].count('href="' + d + '.xhtml"')) > 0:
                        try:
                            self.epubtemp[p] = self.epubtemp[p].replace(
                                'href="' + d + '.xhtml"',
                                'href="nfChapter' + str(self.pageIDDict[d]) + '.xhtml"',
                            )
                        except KeyError:
                            print("Key error at: " + d)
                            print("Please report this error to the developer.")

        if self.pbar:
            self.pbar.End()
        if self.backwards:
            self.epubtemp = self.temp.copy()

        # band-aid fix for names in chapter titles
        # WARNING DO NOT PUT THIS TO PRODUCTION
        for i in range(len(self.chapters)):
            for j in range(len(self.renames)):
                self.chapters[i] = self.chapters[i].replace(
                    self.oldnames[j], self.renames[j]
                )

        # TODO regular expressions go here

        for i in range(len(self.temp)):
            self.temp[i] = "\n<h4>by " + self.authors[i] + "</h4>" + self.temp[i]
            if Common.opf is not None and any(x in ("epub", "EPUB") for x in Common.opf):
                self.epubtemp[i] = (
                    "\n<h4>by " + self.authors[i] + "</h4>" + self.epubtemp[i]
                )
            self.rawstoryhtml.append(BeautifulSoup(self.temp[i], "html.parser"))
            if Common.opf is not None and any(x in ("epub", "EPUB") for x in Common.opf):
                self.epubrawstoryhtml.append(
                    BeautifulSoup(self.epubtemp[i], "html.parser")
                )
        # print(self.rawstoryhtml[len(self.rawstoryhtml)-1].get_text())
        if self.authors:
            self.author = self.authors[0]
        # print(self.chapters)

        # replaces replaceable text in the story
        for i_tag in self.rawstoryhtml:
            for j in range(len(self.renames)):
                for k in i_tag.find_all(
                    "span", attrs={"class": "js-immersion-receiver-c" + str(j)}
                ):
                    k.string = self.renames[j]
            self.story += self.chapters[self.rawstoryhtml.index(i_tag)] + i_tag.get_text()

            self.truestoryhttml.append(str(i_tag))
        if Common.opf is not None and any(x in ("epub", "EPUB") for x in Common.opf):
            for i_tag in self.epubrawstoryhtml:
                for j in range(len(self.renames)):
                    for l_tag in i_tag.find_all(
                        "span", attrs={"class": "js-immersion-receiver-c" + str(j)}
                    ):
                        l_tag.string = self.renames[j]
                self.epubtruestoryhttml.append(str(i_tag))

        for i in range(len(self.truestoryhttml)):
            self.truestoryhttml[i] = self.truestoryhttml[i].replace(
                "\n  <span", "<span"
            )
            self.truestoryhttml[i] = self.truestoryhttml[i].replace("<span", " <span")
            for j_name in self.renames:
                self.truestoryhttml[i] = self.truestoryhttml[i].replace(
                    "\n   " + j_name + "\n", j_name
                )
            self.truestoryhttml[i] = self.truestoryhttml[i].replace(
                "  </span>\n  ", "</span> "
            )

        if Common.opf is not None and any(x in ("epub", "EPUB") for x in Common.opf):
            for i in range(len(self.epubtruestoryhttml)):
                self.epubtruestoryhttml[i] = self.epubtruestoryhttml[i].replace(
                    "\n <span", "<span"
                )
                self.epubtruestoryhttml[i] = self.epubtruestoryhttml[i].replace(
                    "<span", " <span"
                )
                for j_name in self.renames:
                    self.epubtruestoryhttml[i] = self.epubtruestoryhttml[i].replace(
                        "\n   " + j_name + "\n", j_name
                    )
                self.epubtruestoryhttml[i] = self.epubtruestoryhttml[i].replace(
                    "  </span>\n  ", "</span> "
                )

        self.story = self.story.replace("\n", Common.lineEnding)

        for i in range(0, len(self.truestoryhttml)):
            self.rawstoryhtml[i] = BeautifulSoup(self.truestoryhttml[i], "html.parser")

        if Common.opf is not None and any(x in ("epub", "EPUB") for x in Common.opf):
            for i in range(0, len(self.epubtruestoryhttml)):
                self.epubrawstoryhtml[i] = BeautifulSoup(
                    self.epubtruestoryhttml[i], "html.parser"
                )

        if (
            Common.images
            and self.hasimages
            and Common.opf is not None
            and any(x in ("html", "HTML") for x in Common.opf)
        ):
            for i in range(0, len(Common.urlDict[self.url])):
                Common.prnt(
                    "Getting image "
                    + str(i + 1)
                    + " at: "
                    + str(Common.urlDict[self.url][i])
                )
                try:
                    Common.imageDL(
                        self.title,
                        Common.urlDict[self.url][i],
                        i + 1,
                        size=len(Common.urlDict[self.url]),
                    )
                except Exception:
                    continue

    def AddPrevPage(self, url: str) -> Optional[str]:
        page = self.requestPage(url)

        if page is None:
            print("Could not complete request for page: " + url)
            return None

        soup = BeautifulSoup(page.content, "html.parser")
        meta_p = soup.find("p", class_="meta")
        if isinstance(meta_p, Tag):
            meta_a = meta_p.find("a")
            if isinstance(meta_a, Tag):
                self.authors.insert(0, meta_a.get_text())

        h1_tag = soup.find("h1")
        if isinstance(h1_tag, Tag):
            self.chapters.insert(0, h1_tag.get_text())

        if Common.images:
            content_div = soup.find("div", attrs={"class": "chapter-content"})
            if isinstance(content_div, Tag) and content_div.find("img"):
                for simg in content_div.find_all("img"):
                    src = simg.get("src")
                    if isinstance(src, str):
                        self.images.append(src)
                        simg["src"] = "img" + str(len(self.images)) + ".jpg"
                        self.hasimages = True

        content_div = soup.find("div", attrs={"class": "chapter-content"})
        temp = str(content_div) if isinstance(content_div, Tag) else ""
        q_header = soup.find("header", attrs={"class": "question-header"})
        if isinstance(q_header, Tag):
            self.questions.insert(0, q_header.get_text())
        temp += "<h2>" + (self.questions[0] if self.questions else "") + "</h2>"
        self.temp.insert(0, temp)

        if self.pbar:
            self.pbar.Update()
        for i in soup.find_all("a"):
            if i.text.strip() == "Previous Chapter":
                href = i.get("href")
                return href if isinstance(href, str) else None
        # gets author name if on last/first page I guess
        if isinstance(meta_p, Tag):
            meta_a = meta_p.find("a")
            if isinstance(meta_a, Tag):
                self.authors[0] = meta_a.get_text()
        return None

    # def AddNextPage(self, (url, depth, prevChapNum, prevLink, epubPrevLink, currLink, prevLinkId)):
    def AddNextPage(self, args: Any) -> None:
        url = args[0]
        depth = args[1]
        prevChapNum = args[2]
        prevLink = args[3]
        epubPrevLink = args[4]
        currLink = args[5]
        prevLinkId = args[6]

        page = self.requestPage(url)

        if page is None:
            print("Could not complete request for page: " + url)
            return

        soup = BeautifulSoup(page.content, "html.parser")

        try:
            meta_p = soup.find("p", class_="meta")
            if isinstance(meta_p, Tag):
                meta_a = meta_p.find("a")
                if isinstance(meta_a, Tag):
                    self.authors.append(meta_a.get_text())
                else:
                    self.authors.append("Unknown")
            else:
                self.authors.append("Unknown")
        except AttributeError:
            self.authors.append("Unknown")

        h1_tag = soup.find("h1")
        if isinstance(h1_tag, Tag):
            self.chapters.append(h1_tag.get_text())

        epubCurrLink = (
            '\n<a href="'
            + str(depth)
            + '.xhtml">'
            + "Previous Chapter"
            + "</a>\n<br />"
        )

        if Common.images:
            content_div = soup.find("div", attrs={"class": "chapter-content"})
            if isinstance(content_div, Tag) and content_div.find("img"):
                for simg in content_div.find_all("img"):
                    imgtemp = simg.get("src")
                    if isinstance(imgtemp, str):
                        simg["src"] = (
                            "img" + str(len(Common.urlDict[self.ogUrl]) + 1) + ".jpg"
                        )
                        Common.urlDict[self.ogUrl][
                            len(Common.urlDict[self.ogUrl])
                        ] = imgtemp
                        self.hasimages = True

        content_div = soup.find("div", attrs={"class": "chapter-content"})
        self.depth.append(str(depth))
        temp = '<div id="' + str(depth) + '">' + str(content_div)

        try:
            q_header = soup.find("header", attrs={"class": "question-header"})
            if isinstance(q_header, Tag):
                self.questions.append(q_header.get_text())
            else:
                self.questions.append("What's next?")
        except AttributeError:
            self.questions.append("What's next?")

        temp += "<h2>" + self.questions[-1] + "</h2>\n</div>"
        if self.partial:
            Common.prnt(str(depth))
        j = 1

        nextpages = []
        epubnextpages = []
        nextpagesurl = []
        nextpagesdepth = []
        temp += "<br />"
        epubtemp = temp
        q_content = soup.find("div", attrs={"class": "question-content"})
        if isinstance(q_content, Tag):
            for i in q_content.find_all("a"):
                if i.get_text().strip() != "Add a new chapter":
                    link = i.get_text()
                    # Band aid fix for replaceable text in the next chapter links
                    for i_rename in range(len(self.renames)):
                        link = link.replace(self.oldnames[i_rename], self.renames[i_rename])
                    nextLink = (
                        '\n<a href="#'
                        + str(depth)
                        + "."
                        + str(j)
                        + '">'
                        + "Previous Chapter"
                        + "</a>\n<br />"
                    )
                    # nextLinks.append(nextLink)

                    if Common.opf is not None and any(
                        x in ("epub", "EPUB") for x in Common.opf
                    ):
                        epubnextpages.append(
                            '\n<a href="'
                            + str(depth)
                            + "."
                            + str(j)
                            + '.xhtml">'
                            + link.strip()
                            + "</a>\n<br />"
                        )
                    nextpages.append(
                        '\n<a href="#'
                        + str(depth)
                        + "."
                        + str(j)
                        + '">'
                        + link.strip()
                        + "</a>\n<br />"
                    )
                    # nextpages.append(prevLink)
                    nextpagesurl.append(i)
                    nextpagesdepth.append(j)
                    j += 1
        temp += prevLink
        if Common.opf is not None and any(x in ("epub", "EPUB") for x in Common.opf):
            epubtemp += epubPrevLink
            for j_str in epubnextpages:
                epubtemp += j_str
            self.epubtemp.append(epubtemp)

        for j_str in nextpages:
            temp += j_str
        self.temp.append(temp)
        if self.pbar:
            self.pbar.Update()
        # Checks if new page was a link backwards and exits if so
        chapNum = 0
        meta_p = soup.find("p", attrs={"class": "meta"})
        if isinstance(meta_p, Tag):
            meta_text = meta_p.get_text().split()
            if len(meta_text) > 1:
                chapNum = int(meta_text[1])

        self.pageIDs.append(self.pageIDIter)
        self.pageIDDict[depth] = self.pageIDIter
        self.pageIDIter += 1

        if prevChapNum >= chapNum:
            return

        # Other check if current page is a link and doesn't continue if so
        prevLinkCheck1 = soup.find("span", attrs={"class": "controls-left"})
        if isinstance(prevLinkCheck1, Tag):
            a_tags = prevLinkCheck1.find_all("a")
            if a_tags:
                prevLinkCheck2 = a_tags[0].get("href")
                if isinstance(prevLinkCheck2, str):
                    prevLinkId1 = urllib.parse.urlparse(prevLinkCheck2)[2].split(".")[
                        -1
                    ]

                    currLinkId = urllib.parse.urlparse(url)[2].split(".")[-1]
                    if prevLinkId is not None and prevLinkId1 != prevLinkId:
                        return

        n2 = []
        for i_tag, j_int in zip(nextpagesurl, nextpagesdepth, strict=False):
            href = i_tag.get("href")
            if isinstance(href, str):
                n2.append(
                    [
                        href,
                        str(depth) + "." + str(j_int),
                        chapNum,
                        currLink,
                        epubCurrLink,
                        nextLink,
                        currLinkId,
                    ]
                )
        self.pageQueue[0:0] = n2

    def ThreadAdd(
        self,
        url: str,
        depth: str,
        renames: List[str],
        oldnames: List[str],
        chapNum: int,
        currLink: str,
        epubCurrLink: str,
        nextLink: str,
        currLinkId: str,
        ogUrl: str,
    ) -> None:
        try:
            idx = self.Pages.index(url)
            self.Pages[idx] = Page(
                url,
                depth,
                renames,
                oldnames,
                self.q,
                chapNum,
                currLink,
                epubCurrLink,
                nextLink,
                currLinkId,
                ogUrl,
            )
        except ValueError:
            pass

    def addPage(self, page: Any) -> None:
        self.depth.append(page.depth)
        self.authors.append(page.author)
        self.chapters.append(page.chapter)
        self.images.extend(page.images)
        if page.hasimages:
            self.hasimages = True
        self.questions.extend(page.questions)
        self.epubtemp.extend(page.epubtemp)
        self.temp.extend(page.temp)

        self.pageIDs.append(self.pageIDIter)
        self.pageIDDict[page.depth] = self.pageIDIter
        self.pageIDIter += 1

        if page.children != []:
            for zzz in range(0, len(page.children)):
                while isinstance(page.children[zzz], str):
                    self.q.get()
            # prepend child pages to the queue
            self.pageQueue[0:0] = page.children


class Page:
    visitedPages: Dict[str, "Page"] = {}
    children: List[Any]
    depth: str
    author: str
    chapter: str
    images: List[str]
    hasimages: bool
    questions: List[str]
    epubtemp: List[str]
    temp: List[str]
    renames: List[str]
    oldnames: List[str]
    q: queue.Queue[Any]
    chapNum: int
    prevChapNum: int
    prevLink: str
    currLink: str
    epubPrevLink: str
    prevLinkId: Optional[str]
    ogUrl: str

    def __init__(
        self,
        url: str,
        depth: Any,
        renames: List[str],
        oldnames: List[str],
        q: queue.Queue[Any],
        prevChapNum: int,
        prevLink: str,
        epubPrevLink: str,
        currLink: str,
        prevLinkId: Optional[str],
        ogUrl: str,
    ) -> None:
        self.children = []
        self.depth = str(depth)
        self.author = ""
        self.chapter = ""
        self.images = []
        self.hasimages = False
        self.questions = []
        self.epubtemp = []
        self.temp = []
        self.renames = renames
        self.oldnames = oldnames
        self.q = q
        self.chapNum = 0
        self.prevChapNum = prevChapNum
        self.prevLink = prevLink
        self.currLink = currLink
        self.epubPrevLink = epubPrevLink
        self.prevLinkId = prevLinkId

        self.ogUrl = ogUrl

        self.AddNextPage(url, depth)
        self.q.put(self, False)

    def AddNextPage(self, url: str, depth: Any) -> None:
        page = Common.RequestPageChyoa(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}
        )

        if page is None:
            print("Could not complete request for page: " + url)
            return

        soup = BeautifulSoup(page.content, "html.parser")

        try:
            meta_p = soup.find("p", class_="meta")
            if isinstance(meta_p, Tag):
                meta_a = meta_p.find("a")
                if isinstance(meta_a, Tag):
                    self.author = meta_a.get_text()
                else:
                    self.author = "Unknown"
            else:
                self.author = "Unknown"
        except AttributeError:
            self.author = "Unknown"

        h1_tag = soup.find("h1")
        if isinstance(h1_tag, Tag):
            self.chapter = h1_tag.get_text()

        if Common.images:
            content_div = soup.find("div", attrs={"class": "chapter-content"})
            if isinstance(content_div, Tag) and content_div.find("img"):
                with lock2:
                    for simg in content_div.find_all("img"):
                        imgtemp = simg.get("src")
                        if isinstance(imgtemp, str):
                            simg["src"] = (
                                "img" + str(len(Common.urlDict[self.ogUrl]) + 1) + ".jpg"
                            )
                            Common.urlDict[self.ogUrl][
                                len(Common.urlDict[self.ogUrl])
                            ] = imgtemp
                self.hasimages = True

        content_div = soup.find("div", attrs={"class": "chapter-content"})
        Common.prnt(str(depth))
        temp = '<div id="' + str(depth) + '">' + str(content_div)

        try:
            q_header = soup.find("header", attrs={"class": "question-header"})
            if isinstance(q_header, Tag):
                self.questions.append(q_header.get_text())
            else:
                self.questions.append("What's next?")
        except AttributeError:
            self.questions.append("What's next?")

        temp += "<h2>" + self.questions[-1] + "</h2>\n</div>"
        j = 1

        nextpages = []
        epubnextpages = []
        nextpagesurl = []
        nextpagesdepth = []
        urls = []
        temp += "<br />"
        epubtemp = temp
        nextLinks: List[str] = []
        epubCurrLink = (
            '\n<a href="'
            + str(depth)
            + '.xhtml">'
            + "Previous Chapter"
            + "</a>\n<br />"
        )

        temp += self.prevLink

        q_content = soup.find("div", attrs={"class": "question-content"})
        if isinstance(q_content, Tag):
            for i in q_content.find_all("a"):
                if i.get_text().strip() != "Add a new chapter":
                    link = i.get_text()
                    # Band aid fix for replaceable text in the next chapter links
                    for i_rename in range(len(self.renames)):
                        link = link.replace(self.oldnames[i_rename], self.renames[i_rename])

                    if Common.opf is not None and any(
                        x in ("epub", "EPUB") for x in Common.opf
                    ):
                        epubnextpages.append(
                            '\n<a href="'
                            + str(depth)
                            + "."
                            + str(j)
                            + '.xhtml">'
                            + link.strip()
                            + "</a>\n<br />"
                        )
                    nextLink = (
                        '\n<a href="#'
                        + str(depth)
                        + "."
                        + str(j)
                        + '">'
                        + "Previous Chapter"
                        + "</a>\n<br />"
                    )
                    nextLinks.append(nextLink)
                    nextpages.append(
                        '\n<a href="#'
                        + str(depth)
                        + "."
                        + str(j)
                        + '">'
                        + link.strip()
                        + "</a>\n<br />"
                    )
                    nextpagesurl.append(i)
                    href = i.get("href")
                    if isinstance(href, str):
                        urls.append(href)
                    nextpagesdepth.append(j)
                    j += 1

        if Common.opf is not None and any(x in ("epub", "EPUB") for x in Common.opf):
            epubtemp += self.epubPrevLink
            for j_str in epubnextpages:
                epubtemp += j_str
            self.epubtemp.append(epubtemp)

        for j_str in nextpages:
            temp += j_str
        self.temp.append(temp)

        # Checks if new page was a link backwards and exits if so
        self.chapNum = 0
        meta_p = soup.find("p", attrs={"class": "meta"})
        if isinstance(meta_p, Tag):
            meta_text = meta_p.get_text().split()
            if len(meta_text) > 1:
                self.chapNum = int(meta_text[1])

        if self.prevChapNum >= self.chapNum:
            return

        # Other check if current page is a link and doesn't continue if so
        prevLinkCheck1 = soup.find("span", attrs={"class": "controls-left"})
        if isinstance(prevLinkCheck1, Tag):
            a_tags = prevLinkCheck1.find_all("a")
            if a_tags:
                prevLinkCheck2 = a_tags[0].get("href")
                if isinstance(prevLinkCheck2, str):
                    prevLinkId = urllib.parse.urlparse(prevLinkCheck2)[2].split(".")[
                        -1
                    ]

                    currLinkId = urllib.parse.urlparse(url)[2].split(".")[-1]
                    if self.prevLinkId is not None and prevLinkId != self.prevLinkId:
                        return

        self.children.extend(urls)
        for idx in range(0, len(nextpagesurl)):
            href = nextpagesurl[idx].get("href")
            if isinstance(href, str):
                threading.Thread(
                    target=self.ThreadAdd,
                    args=(
                        href,
                        str(depth) + "." + str(nextpagesdepth[idx]),
                        self.renames,
                        self.oldnames,
                        self.currLink,
                        epubCurrLink,
                        nextLinks[idx],
                        currLinkId,
                    ),
                    daemon=True,
                ).start()

    def ThreadAdd(
        self,
        url: str,
        depth: str,
        renames: List[str],
        oldnames: List[str],
        currLink: str,
        epubCurrLink: str,
        nextLink: str,
        currLinkId: str,
    ) -> None:
        try:
            idx = self.children.index(url)
            self.children[idx] = self.__class__(
                url,
                depth,
                renames,
                oldnames,
                self.q,
                self.chapNum,
                currLink,
                epubCurrLink,
                nextLink,
                currLinkId,
                self.ogUrl,
            )
        except ValueError:
            pass
