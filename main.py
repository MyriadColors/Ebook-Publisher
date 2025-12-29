#!/usr/bin/env python3
import argparse
import getpass
import os
import queue
import sys
import threading
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from zipfile import ZipFile

from EpubMaker import epub as epub
from Site import Chyoa, Classicreader, Common, Fanfiction, Literotica, Nhentai, Wattpad

Version = "3.4.0"

# Master dict of supported sites
sites: Dict[str, Callable[[str], Common.SiteProvider]] = {
    "www.literotica.com": lambda x: Literotica.Literotica(x),
    "www.fanfiction.net": lambda x: Fanfiction.Fanfiction(x),
    "www.fictionpress.com": lambda x: Fanfiction.Fanfiction(x),
    "www.classicreader.com": lambda x: Classicreader.Classicreader(x),
    "chyoa.com": lambda x: Chyoa.Chyoa(x),
    "www.wattpad.com": lambda x: Wattpad.Wattpad(x),
    "nhentai.net": lambda x: Nhentai.Nhentai(x),
}
formats: Dict[str, Callable[[Common.SiteProvider], None]] = {
    "epub": lambda x: MakeEpub(x),
    "html": lambda x: MakeHTML(x),
    "txt": lambda x: MakeText(x),
    "EPUB": lambda x: MakeEpub(x),
    "HTML": lambda x: MakeHTML(x),
    "TXT": lambda x: MakeText(x),
}


# function for making text files
def MakeText(site: Common.SiteProvider) -> None:
    if not isinstance(site, Nhentai.Nhentai):
        title_stripped = Common.sanitize_filename(site.title)
        published = open(
            os.path.join(wd, title_stripped + ".txt"), "w", encoding="utf-8"
        )
        published.write(site.title + Common.lineEnding)
        published.write("by " + site.author + Common.lineEnding)
        published.write(site.story)
        published.close()

def MakeHTML(site: Any) -> None:
    title_stripped = Common.sanitize_filename(site.title)
    if (isinstance(site, (Chyoa.Chyoa, Nhentai.Nhentai))) and site.hasimages:
        published = open(
            os.path.join(wd, title_stripped, title_stripped + ".html"),
            "w",
            encoding="utf-8",
        )
    else:
        published = open(
            os.path.join(wd, title_stripped + ".html"), "w", encoding="utf-8"
        )
    published.write("<!DOCTYPE html>\n")
    published.write('<html lang="en">')
    published.write("<style>\n" + styleSheet + "\n</style>")
    published.write(
        "<head>\n<title>"
        + Common.escape_html(site.title)
        + " by "
        + Common.escape_html(site.author)
        + "</title>\n</head>\n"
    )
    published.write(
        "<h1>"
        + Common.escape_html(site.title)
        + "</h1><h3>by "
        + Common.escape_html(site.author)
        + "</h3><br /><a href="
        + Common.escape_html(site.url)
        + ">"
        + Common.escape_html(site.url)
        + "</a>\n"
    )
    if not isinstance(site, (Nhentai.Nhentai, Literotica.Literotica)):
        published.write("<h2>Table of Contents</h2>\n")
        if not isinstance(site, Chyoa.Chyoa):
            for i in range(len(site.rawstoryhtml)):
                published.write(
                    '<p><a href="#Chapter ' \
                    + str(i)
                    + '">'
                    + Common.escape_html(site.chapters[i])
                    + "</a></p>\n"
                )
        elif not site.backwards:
            j = 0
            for i in range(len(site.rawstoryhtml)):
                if i != 0:
                    if site.partial:
                        published.write(
                            '<p><a href="#'
                            + str(site.depth[i - 1])
                            + '">'
                            + str(" _" * int((len(site.depth[i - 1]) / 2) + 1))
                            + " "
                            + str(
                                int(
                                    (site.partialStart + len(site.depth[i - 1]) / 2) + 1
                                )
                            )
                            + "."
                            + site.depth[i - 1].split(".")[-1]
                            + " "
                            + Common.escape_html(site.chapters[i])
                            + "</a></p>\n"
                        )
                    else:
                        published.write(
                            '<p><a href="#'
                            + str(site.depth[i - 1])
                            + '">'
                            + str(" _" * int((len(site.depth[i - 1]) / 2) + 1))
                            + " "
                            + str(int((len(site.depth[i - 1]) / 2) + 2))
                            + "."
                            + site.depth[i - 1].split(".")[-1]
                            + " "
                            + Common.escape_html(site.chapters[i])
                            + "</a></p>\n"
                        )
                else:
                    if site.partial:
                        j = site.partialStart
                        published.write(
                            '<p><a href="#Chapter ' \
                            + str(i)
                            + '">'
                            + str(j)
                            + ". "
                            + Common.escape_html(site.chapters[i])
                            + "</a></p>\n"
                        )
                        j += 1
                    else:
                        published.write(
                            '<p><a href="#Chapter ' \
                            + str(i)
                            + '">'
                            + "1.1 "
                            + Common.escape_html(site.chapters[i])
                            + "</a></p>\n"
                        )
        else:
            for i in range(len(site.rawstoryhtml)):
                published.write(
                    '<p><a href="#Chapter ' \
                    + str(i)
                    + '">'
                    + Common.escape_html(site.chapters[i])
                    + "</a></p>\n"
                )
    for i in range(len(site.rawstoryhtml)):
        if isinstance(site, Nhentai.Nhentai):
            published.write(Common.sanitize_html(site.truestoryhttml[i]))
        elif isinstance(site, Literotica.Literotica):
            published.write(Common.sanitize_html(site.storyhtml))
            break
        else:
            if isinstance(site, Chyoa.Chyoa) and not site.backwards:
                if i != 0:
                    published.write(
                        '<h2 id = "'
                        + site.depth[i - 1]
                        + '">'
                        + Common.escape_html(site.chapters[i])
                        + "\n</h2>\n"
                        + Common.sanitize_html(site.rawstoryhtml[i])
                    )
                else:
                    published.write(
                        '<h2 id="Chapter ' \
                        + str(i)
                        + '">\n'
                        + Common.escape_html(site.chapters[i])
                        + "\n</h2>\n"
                        + Common.sanitize_html(site.rawstoryhtml[i])
                    )
            else:
                published.write(
                    '<h2 id="Chapter ' \
                    + str(i)
                    + '">\n'
                    + Common.escape_html(site.chapters[i])
                    + "\n</h2>\n"
                    + Common.sanitize_html(site.rawstoryhtml[i])
                )
    published.write("</html>")

    published.close()


# def GetImage(url):
# req = urllib.request.Request(url, headers={'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'})
# return urllib.request.urlopen(req).read()


# This function is basically all magic from the docs of EpubMaker
def MakeEpub(site: Any) -> None:
    book = epub.EpubBook()
    book.set_identifier(Common.escape_html(site.url))
    titlepage = epub.EpubHtml(title="Title Page", file_name="Title.xhtml", lang="en")
    titlepage.content = (
        "<h1>"
        + Common.escape_html(site.title)
        + "</h1><h3>by "
        + Common.escape_html(site.author)
        + "</h3><br /><a href="
        + Common.escape_html(site.url)
        + ">"
        + Common.escape_html(site.url)
        + "</a>"
    )
    # add summary information
    if hasattr(site, "summary"):
        titlepage.content += "<br /><p>" + Common.sanitize_html(site.summary) + "</p>"
    book.add_item(titlepage)
    book.spine = [titlepage]
    book.set_title(Common.escape_html(site.title))
    book.set_language("en")
    book.add_author(Common.escape_html(site.author))
    book.add_style_sheet(styleSheet)
    c: List[epub.EpubHtml] = []

    if not isinstance(site, (Literotica.Literotica, Nhentai.Nhentai)):
        toc: List[epub.EpubHtml] = []
        for i in range(len(site.rawstoryhtml)):
            if isinstance(site, Chyoa.Chyoa) and not site.backwards:
                if i == 0:
                    c.append(
                        epub.EpubHtml(
                            title=Common.escape_html(site.chapters[i]),
                            file_name="Chapter " + str(i + 1) + ".xhtml",
                            lang="en",
                        )
                    )
                else:
                    if not site.partial:
                        c.append(
                            epub.EpubHtml(
                                title=Common.escape_html(site.chapters[i]),
                                file_name="nfChapter"
                                + str(site.pageIDs[i - 1])
                                + ".xhtml",
                                lang="en",
                                tocTitle=str(
                                    " _" * int((len(site.depth[i - 1]) / 2) + 1)
                                )
                                + " "
                                + str(int((len(site.depth[i - 1]) / 2) + 2))
                                + "."
                                + site.depth[i - 1].split(".")[-1]
                                + " "
                                + Common.escape_html(site.chapters[i]),
                            )
                        )
                        # c.append(epub.EpubHtml(title=site.chapters[i], file_name=str(site.depth[i-1])+'.xhtml', lang='en', tocTitle=str(' _'*int((len(site.depth[i-1])/2)+1))+' '+str(int((len(site.depth[i-1])/2)+2))+'.'+site.depth[i-1].split('.')[-1]+' '+site.chapters[i]))
                    else:
                        c.append(
                            epub.EpubHtml(
                                title=Common.escape_html(site.chapters[i]),
                                file_name="nfChapter"
                                + str(site.pageIDs[i - 1])
                                + ".xhtml",
                                lang="en",
                                tocTitle=str(
                                    " _" * int((len(site.depth[i - 1]) / 2) + 1)
                                )
                                + " "
                                + str(
                                    int(
                                        (site.partialStart + len(site.depth[i - 1]) / 2)
                                        + 1
                                    )
                                )
                                + "."
                                + site.depth[i - 1].split(".")[-1]
                                + " "
                                + Common.escape_html(site.chapters[i]),
                            )
                        )
                c[i].content = (
                    "<h2>\n"
                    + Common.escape_html(site.chapters[i])
                    + "\n</h2>\n"
                    + Common.sanitize_html(site.epubrawstoryhtml[i])
                )
            elif isinstance(site, Nhentai.Nhentai):
                c.append(
                    epub.EpubHtml(
                        title=Common.escape_html(site.chapters[i]),
                        file_name="Chapter " + str(i + 1) + ".xhtml",
                        lang="en",
                    )
                )
                c[i].content = Common.sanitize_html(site.truestoryhttml[i])
            else:
                c.append(
                    epub.EpubHtml(
                        title=Common.escape_html(site.chapters[i]),
                        file_name="Chapter " + str(i + 1) + ".xhtml",
                        lang="en",
                    )
                )
                c[i].content = (
                    "<h2>\n"
                    + Common.escape_html(site.chapters[i])
                    + "\n</h2>\n"
                    + Common.sanitize_html(site.rawstoryhtml[i])
                )
            book.add_item(c[i])
            toc.append(c[i])

        book.toc = toc
        book.spine.append("nav")
    elif isinstance(site, Nhentai.Nhentai):
        c.append(epub.EpubHtml(title="none", file_name="Chapter 1.xhtml", lang="en"))
        c[0].content = Common.sanitize_html(site.truestoryhttml[0])
        book.add_item(c[0])
        book.spine.append("nav")

    # fallback method
    else:
        c.append(
            epub.EpubHtml(
                title=Common.escape_html(site.title), file_name="Story.xhtml", lang="en"
            )
        )
        c[0].content = Common.sanitize_html(site.storyhtml)
        book.add_item(c[0])
        # print(site.title)
    # more ebooklib space magic
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    # book.spine.append('nav')
    for item in c:
        book.spine.append(item)
    title_stripped = Common.sanitize_filename(site.title)
    epub.write_epub(os.path.join(wd, title_stripped + ".epub"), book)

    if isinstance(site, Nhentai.Nhentai):
        if site.hasimages:
            with ZipFile(os.path.join(wd, site.title + ".epub"), "a") as myfile:
                i = 1
                for url in site.images:
                    zeros = "0" * (len(str(len(site.images))) - 1)
                    if len(zeros) > 1 and i > 9:
                        zeros = "0"
                    elif len(zeros) == 1 and i > 9:
                        zeros = ""
                    if i > 99:
                        zeros = ""
                    with myfile.open("EPUB/" + zeros + str(i) + ".jpg", "w") as myimg:
                        img_data = Common.GetImage(url)
                        if img_data is not None:
                            myimg.write(img_data)
                    i = i + 1
    elif isinstance(site, Chyoa.Chyoa):
        if site.hasimages:
            with ZipFile(os.path.join(wd, title_stripped + ".epub"), "a") as myfile:
                i = 1
                for num in Common.urlDict[site.url]:
                    try:
                        i = i + 1
                        with myfile.open(
                            "EPUB/img" + str(i - 1) + ".jpg", "w"
                        ) as myimg:
                            img_data = Common.GetImage(Common.urlDict[site.url][num])
                            if img_data is not None:
                                myimg.write(img_data)
                    except Exception:
                        continue

def MakeClass(url: str) -> Optional[Common.SiteProvider]:
    # getting url
    domain = urllib.parse.urlparse(url)[1]
    if domain == "nhentai.net" and args.t:
        # TODO the lock should be in the Nhentai class definitions
        with lock:
            site = sites[domain](url)
    else:
        try:
            site = sites[domain](url)
        except KeyError:
            print("Unsupported site: " + domain)
            return None
    # site=sites[domain](url)
    if args.t:
        if not site.duplicate:
            for ft in ftype:
                formats[ft](site)
            q.put(site)
        else:
            return None
    return site


# grabs all of the urls if the argument is a file, or assumes the argument is a single URL
def ListURLs(url: str) -> Union[List[str], Tuple[str, ...]]:
    if os.path.isfile(os.path.join(cwd, url)):
        with open(cwd + "/" + url, "r") as fi:
            return fi.read().splitlines()
    else:
        return (url,)

def getCSS() -> str:
    if os.path.isfile(os.path.join(cwd, args.css)):
        with open(cwd + "/" + args.css, "r") as fi:
            return fi.read()
    else:
        return str(args.css)


# setting up commandline argument parser


parser = argparse.ArgumentParser(
    description="Ebook-Publisher: Convert stories from various websites into EPUB, HTML, or TXT formats.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""



Authentication (Chyoa):



  Securely provide credentials using environment variables:



    CHYOA_USER=username



    CHYOA_PASSWORD=password






    Alternatively, provide --usr to be prompted for a password interactively.





  """,
)


parser.add_argument("url", help="The URL of the story you want", nargs="*")


parser.add_argument(
    "-o",
    "--output-type",
    help="The file type you want",
    choices=["txt", "epub", "html", "TXT", "EPUB", "HTML"],
    action="append",
)


# parser.add_argument('-f','--file', help="Does nothing! Previously denoted the use of a text file containing a list of URLs instead of single URL", action='store_true')


parser.add_argument(
    "-d", "--directory", help="Directory to place output files. Default ./'"
)


parser.add_argument(
    "-q", "--quiet", help="Turns off most terminal output", action="store_true"
)


parser.add_argument(
    "-t",
    help="Turns on multithreading mode. Recommend also enabling --quiet",
    action="store_true",
)


parser.add_argument(
    "-i",
    "--insert-images",
    help="Downloads and inserts images for Chyoa stories",
    action="store_true",
)


parser.add_argument(
    "-n",
    "--no-duplicates",
    help="Skips stories if they have already been downloaded",
    action="store_true",
)


parser.add_argument(
    "-s",
    "--css",
    "--style-sheet",
    help="either a CSS string or a .css file to use for formatting",
    default="",
)


parser.add_argument(
    "--chyoa-force-forwards",
    help="Force Chyoa stories to be scraped forwards if not given page 1",
    action="store_true",
)


parser.add_argument(
    "--eol",
    help="end of line character for .txt output format, must be enclosed in single quotes",
    default="\n\n",
)


parser.add_argument(
    "--chyoa-update",
    help="Checks if story already exists in output directory, and skips it if it has not been updated on the server since file was created.",
    action="store_true",
)


parser.add_argument(
    "--usr",
    help="Chyoa username. If provided, you will be prompted for a password securely.",
)


args = parser.parse_args()


# Handle credentials securely


password = os.environ.get("CHYOA_PASSWORD")


user = args.usr or os.environ.get("CHYOA_USER")


if user:
    Common.chyoa_name = user

    if not password:
        password = getpass.getpass(f"Password for Chyoa user '{user}': ")

try:
    if user and password:
        Common.GetChyoaSession(password)


except Common.AuthenticationError as e:
    print(f"Error: {e}")

    sys.exit(1)


if args.quiet:
    Common.quiet = True
    # sys.stdout=open(os.devnull, 'w')
    # print('quiet enabled')
if args.insert_images:
    Common.images = True
args.file = True
stdin = False

Common.prnt("Ebook-Publisher " + str(Version))
if not sys.stdin.isatty():
    stdin = True
elif not args.url:
    # print(args.url)
    parser.error("No input")

if args.no_duplicates:
    Common.dup = True

if args.chyoa_force_forwards:
    Common.chyoa_force_forwards = True

if args.chyoa_update:
    Common.chyoaDupCheck = True

Common.lineEnding = args.eol.encode("latin-1", "backslashreplace").decode(
    "unicode-escape"
)

if args.directory is None:
    wd = "./"
else:
    wd = args.directory
Common.wd = wd

Common.opf = args.output_type
if not Common.opf:
    Common.opf = ["txt"]


Common.mt = args.t

cwd = os.getcwd()
# TODO should use non-relative path
wd = os.path.join(cwd, wd)
if not os.path.exists(wd):
    os.makedirs(wd)


styleSheet = getCSS()

ftype = args.output_type
if not ftype:
    ftype = ["txt"]
q: queue.Queue[Common.SiteProvider] = queue.Queue()


if args.file:
    urls: List[str] = []
    # gets the list of urls
    if not stdin:
        for arg in args.url:
            urls.extend(ListURLs(arg))
    else:
        stdinput = sys.stdin.read()
        urls = stdinput.split()

    urls = list(set(urls))

    for url in urls:
        Common.urlDict[url] = {}

    threads = 0
    # the multithreaded variant
    if args.t:
        lock = threading.Lock()
        # Limit concurrent threads to 5 to avoid overwhelming servers/local resources
        semaphore = threading.Semaphore(5)

        def ThreadedMakeClass(url: str) -> None:
            with semaphore:
                MakeClass(url)

        threads = len(urls)
        for i in urls:
            t = threading.Thread(target=ThreadedMakeClass, args=(i,), daemon=False)
            t.start()

    else:
        for i in urls:
            clas = MakeClass(i)
            if clas is not None:
                if not clas.duplicate:
                    for ft in ftype:
                        formats[ft](clas)

    while threads > 1:
        q.get()
        threads -= 1
