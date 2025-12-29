import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, List, Optional, Union
from zipfile import ZipFile

if TYPE_CHECKING:
    pass

version: str = "Epub-Maker 0.3"
MIMETYPE: str = "application/epub+zip"
container: str = """<container xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\" version=\"1.0\">
<rootfiles>
<rootfile media-type=\"application/oebps-package+xml\" full-path=\"EPUB/content.opf\"/>
</rootfiles>
</container>"""


class EpubHtml:
    title: str
    file_name: str
    lang: str
    content: str
    tocTitle: str

    def __init__(
        self,
        title: str = "Title",
        file_name: str = "file_name.xhtml",
        lang: str = "en",
        tocTitle: Optional[str] = None,
    ) -> None:
        self.title = title
        self.file_name = file_name
        self.lang = lang
        self.content = ""
        self.tocTitle = tocTitle if tocTitle is not None else self.title


class EpubNcx:
    pass


class EpubNav:
    pass


EpubItem = Union[EpubHtml, EpubNcx, EpubNav]


class EpubBook:
    item_list: List[EpubItem]
    spine: List[Union[EpubHtml, str]]
    toc: List[EpubHtml]
    author: str
    styleString: str
    identifier: str
    title: str
    language: str

    def __init__(self) -> None:
        self.item_list = []
        self.spine = []
        self.toc = []
        self.author = ""
        self.styleString = ""
        self.identifier = ""
        self.title = ""
        self.language = "en"

    def set_identifier(self, identifier: str) -> None:
        self.identifier = identifier

    def add_item(self, item: EpubItem) -> None:
        self.item_list.append(item)

    def set_title(self, title: str) -> None:
        self.title = title

    def set_language(self, lang: str) -> None:
        self.language = lang

    def add_author(self, author: str) -> None:
        self.author = author

    def add_style_sheet(self, styleString: str) -> None:
        self.styleString = styleString


def _indent(elem: ET.Element, level: int = 0) -> None:
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            _indent(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def write_epub(title: str, book: EpubBook) -> None:
    with ZipFile(title, "w") as Zip:
        Zip.writestr("mimetype", MIMETYPE)
        Zip.writestr("META-INF/container.xml", container)

        # Build content.opf
        package = ET.Element(
            "package",
            {
                "xmlns": "http://www.idpf.org/2007/opf",
                "unique-identifier": "id",
                "version": "3.0",
                "prefix": "rendition: http://www.idpf.org/vocab/rendition/#",
            },
        )

        metadata = ET.SubElement(
            package,
            "metadata",
            {
                "xmlns:dc": "http://purl.org/dc/elements/1.1/",
                "xmlns:opf": "http://www.idpf.org/2007/opf",
            },
        )

        ET.SubElement(metadata, "meta", {"name": "generator", "content": version})
        dc_id = ET.SubElement(metadata, "dc:identifier", {"id": "id"})
        dc_id.text = book.identifier
        dc_title = ET.SubElement(metadata, "dc:title")
        dc_title.text = book.title
        dc_lang = ET.SubElement(metadata, "dc:language")
        dc_lang.text = book.language
        dc_creator = ET.SubElement(metadata, "dc:creator", {"id": "creator"})
        dc_creator.text = book.author

        manifest = ET.SubElement(package, "manifest")
        spine = ET.SubElement(package, "spine", {"toc": "ncx"})

        isTOC = bool(book.toc)

        html_template = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" xml:lang="{lang}">
<head>
<title>{title}</title>
<link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>{content}</body>
</html>"""

        chapter_idx = 0
        for item in book.item_list:
            if isinstance(item, EpubHtml):
                file_content = html_template.format(
                    lang=item.lang, title=item.title, content=item.content
                )
                Zip.writestr("EPUB/" + item.file_name, file_content)
                ET.SubElement(
                    manifest,
                    "item",
                    {
                        "href": item.file_name,
                        "id": f"chapter_{chapter_idx}",
                        "media-type": "application/xhtml+xml",
                    },
                )
                chapter_idx += 1
            elif isinstance(item, EpubNcx):
                ET.SubElement(
                    manifest,
                    "item",
                    {
                        "href": "toc.ncx",
                        "id": "ncx",
                        "media-type": "application/x-dtbncx+xml",
                    },
                )
                # Build NCX
                ncx = ET.Element(
                    "ncx",
                    {
                        "xmlns": "http://www.daisy.org/z3986/2005/ncx/",
                        "version": "2005-1",
                    },
                )
                head = ET.SubElement(ncx, "head")
                ET.SubElement(
                    head, "meta", {"name": "dtb:uid", "content": book.identifier}
                )
                ET.SubElement(head, "meta", {"name": "dtb:depth", "content": "0"})
                ET.SubElement(
                    head, "meta", {"name": "dtb:totalPageCount", "content": "0"}
                )
                ET.SubElement(
                    head, "meta", {"name": "dtb:maxPageNumber", "content": "0"}
                )

                docTitle = ET.SubElement(ncx, "docTitle")
                ET.SubElement(docTitle, "text").text = book.title

                navMap = ET.SubElement(ncx, "navMap")
                if isTOC:
                    for j, toc_item in enumerate(book.toc, 1):
                        navPoint = ET.SubElement(
                            navMap, "navPoint", {"id": f"chapter_{j}"}
                        )
                        navLabel = ET.SubElement(navPoint, "navLabel")
                        ET.SubElement(navLabel, "text").text = toc_item.title
                        ET.SubElement(navPoint, "content", {"src": toc_item.file_name})

                ncx_str = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(
                    ncx, encoding="unicode"
                )
                Zip.writestr("EPUB/toc.ncx", ncx_str)

            elif isinstance(item, EpubNav):
                ET.SubElement(
                    manifest,
                    "item",
                    {
                        "href": "nav.xhtml",
                        "id": "nav",
                        "media-type": "application/xhtml+xml",
                        "properties": "nav",
                    },
                )
                # Build NAV
                nav_html = ET.Element(
                    "html",
                    {
                        "xmlns": "http://www.w3.org/1999/xhtml",
                        "xmlns:epub": "http://www.idpf.org/2007/ops",
                        "lang": "en",
                        "xml:lang": "en",
                    },
                )
                nav_head = ET.SubElement(nav_html, "head")
                ET.SubElement(nav_head, "title").text = book.title
                ET.SubElement(
                    nav_head,
                    "link",
                    {"rel": "stylesheet", "type": "text/css", "href": "style.css"},
                )

                nav_body = ET.SubElement(nav_html, "body")
                nav_tag = ET.SubElement(
                    nav_body, "nav", {"id": "id", "role": "doc-toc", "epub:type": "toc"}
                )
                ET.SubElement(nav_tag, "h2").text = book.title
                ol = ET.SubElement(nav_tag, "ol")
                if isTOC:
                    for toc_item in book.toc:
                        li = ET.SubElement(ol, "li")
                        a = ET.SubElement(li, "a", {"href": toc_item.file_name})
                        a.text = toc_item.tocTitle

                nav_str = (
                    '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
                    + ET.tostring(nav_html, encoding="unicode")
                )
                Zip.writestr("EPUB/nav.xhtml", nav_str)

        chapter_idx = 0
        for spine_item in book.spine:
            if isinstance(spine_item, EpubHtml):
                ET.SubElement(spine, "itemref", {"idref": f"chapter_{chapter_idx}"})
                chapter_idx += 1
            elif spine_item == "nav":
                ET.SubElement(spine, "itemref", {"idref": "nav"})

        opf_str = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(
            package, encoding="unicode"
        )
        Zip.writestr("EPUB/content.opf", opf_str)
        Zip.writestr("EPUB/style.css", book.styleString)


if __name__ == "__main__":
    print(
        "You have mistakenly run this file, epub.py. It is not meant to be run. It must be imported by another python file."
    )
