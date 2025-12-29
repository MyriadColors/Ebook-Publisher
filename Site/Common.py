import sys
import os
import requests
import time
import html
import nh3
from datetime import datetime

# Module contains common functions needed by sites

lineEnding = "\n\n"

quiet = False

images = False

wd = "./"

opf = ("txt",)

epub = ("epub", "Epub", "EPUB")

dup = False

chyoaDupCheck = False

chyoa_force_forwards = False

chyoa_name = None
chyoa_session = None
# Modern User-Agent (Chrome on Windows 10)
default_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

mt = False

urlDict = {}


def sanitize_filename(filename):
    """Sanitizes a string to be used as a safe filename."""
    import re

    # Remove null bytes and other control characters
    filename = "".join(ch for ch in filename if ord(ch) >= 32)
    # Replace known problematic characters with a safe underscore
    # Remove path separators, Windows illegal characters, and hidden characters
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # Remove dot-dot sequences to prevent path traversal
    while ".." in filename:
        filename = filename.replace("..", "_")
    # Strip leading/trailing whitespace and dots which can be used for traversal on Windows
    filename = filename.strip(". ")
    # Ensure it's not an empty string or just underscores
    if not filename or re.match(r"^_+$", filename):
        filename = "story_output"
    return os.path.basename(filename)


def escape_html(text):
    """Escapes HTML special characters in a string."""
    return html.escape(str(text))


def sanitize_html(content):
    """Sanitizes HTML content to remove dangerous tags and attributes."""
    # Define tags that are generally safe for ebooks
    allowed_tags = {
        "a",
        "b",
        "blockquote",
        "br",
        "cite",
        "code",
        "dd",
        "dl",
        "dt",
        "em",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "i",
        "img",
        "li",
        "ol",
        "p",
        "pre",
        "q",
        "small",
        "span",
        "strong",
        "sub",
        "sup",
        "u",
        "ul",
    }
    allowed_attributes = {
        "a": {"href", "title"},
        "img": {"src", "alt", "title", "width", "height"},
        "*": {"id", "class"},
    }
    return nh3.clean(str(content), tags=allowed_tags, attributes=allowed_attributes)


def prnt(out, f=False):
    if not quiet or f:
        print(out)


def is_safe_url(url):
    """Validates that a URL uses a safe scheme and belongs to a supported domain."""
    from urllib.parse import urlparse

    # Whitelist of supported domains (based on sites dict in Ebook-Publisher.py)
    allowed_domains = {
        "www.literotica.com",
        "www.fanfiction.net",
        "www.fictionpress.com",
        "www.classicreader.com",
        "chyoa.com",
        "www.wattpad.com",
        "nhentai.net",
        "cdn.chyoa.com",
        "i.nhentai.net",
        "t.nhentai.net",  # CDNs for images
    }
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if parsed.netloc not in allowed_domains:
            # Allow subdomains for flexibility if needed, or stick to exact match
            return (
                any(parsed.netloc.endswith("." + domain) for domain in allowed_domains)
                or parsed.netloc in allowed_domains
            )
        return True
    except:
        return False


def imageDL(title, url, num, size=0, pbar=None, queue=None):
    title_stripped = sanitize_filename(title)
    target_dir = os.path.join(wd, title_stripped)
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
        except FileExistsError:
            pass
    zeros = "0" * (len(str(size)) - 1)
    # print(zeros)
    if len(zeros) > 1 and num > 9:
        zeros = "0"
    elif len(zeros) == 1 and num > 9:
        zeros = ""
    if num > 99:
        zeros = ""
    if pbar is None:
        zeros = "img"  # TODO fix this for Chyoa stories so that image files don't have to be prepended with 'img' and no zeros
    # print(zeros)
    file_path = os.path.join(target_dir, zeros + str(num) + ".jpg")
    imgbytes = GetImage(url)
    if imgbytes is not None:
        with open(file_path, "wb") as myimg:
            myimg.write(imgbytes)

    if pbar is not None:
        pbar.Update()
    if queue is not None:
        queue.put(num)


def CheckDuplicate(title):
    title_stripped = sanitize_filename(title)
    if any(x in ("epub", "EPUB") for x in opf):
        return os.path.isfile(os.path.join(wd, title_stripped + ".epub"))
    elif any(x in ("txt", "TXT") for x in opf):
        return os.path.isfile(
            os.path.join(wd, title_stripped + ".txt")
        ) or os.path.exists(os.path.join(wd, title_stripped))
    elif any(x in ("html", "HTML") for x in opf):
        return os.path.isfile(
            os.path.join(wd, title_stripped + ".html")
        ) or os.path.exists(os.path.join(wd, title_stripped))


def CheckDuplicateTime(title, timeObject):
    title_stripped = sanitize_filename(title)
    if any(x in ("epub", "EPUB") for x in opf):
        file_path = os.path.join(wd, title_stripped + ".epub")
        if os.path.isfile(file_path):
            if timeObject > datetime.strptime(
                time.ctime(os.path.getmtime(file_path)), "%a %b %d %H:%M:%S %Y"
            ):
                return True
    elif any(x in ("txt", "TXT") for x in opf):
        file_path = os.path.join(wd, title_stripped + ".txt")
        dir_path = os.path.join(wd, title_stripped)
        if os.path.isfile(file_path):
            if timeObject > datetime.strptime(
                time.ctime(os.path.getmtime(file_path)), "%a %b %d %H:%M:%S %Y"
            ):
                return True
        elif os.path.exists(dir_path):
            if timeObject > datetime.strptime(
                time.ctime(os.path.getmtime(dir_path)), "%a %b %d %H:%M:%S %Y"
            ):
                return True

    elif any(x in ("html", "HTML") for x in opf):
        file_path = os.path.join(wd, title_stripped + ".html")
        dir_path = os.path.join(wd, title_stripped)
        if os.path.isfile(file_path):
            if timeObject > datetime.strptime(
                time.ctime(os.path.getmtime(file_path)), "%a %b %d %H:%M:%S %Y"
            ):
                return True
        elif os.path.exists(dir_path):
            if timeObject > datetime.strptime(
                time.ctime(os.path.getmtime(dir_path)), "%a %b %d %H:%M:%S %Y"
            ):
                return True
    return False


def GetImage(url):
    if not is_safe_url(url):
        prnt(f"Blocked unsafe or unsupported URL: {url}")
        return None
    try:
        response = requests.get(url, headers=default_headers, timeout=10)
        if response.status_code == 200:
            return response.content
    except Exception:
        # Fallback logic for extensions if needed
        try:
            new_url = ""
            if url[-4:] == ".jpg":
                new_url = url[:-4] + ".png"
            elif url[-4:] == ".png":
                new_url = url[:-4] + ".jpg"

            if new_url and is_safe_url(new_url):
                response = requests.get(new_url, headers=default_headers, timeout=10)
                if response.status_code == 200:
                    return response.content
        except:
            pass
    return None


class Progress:
    def __init__(self, size):
        # size=0
        self.it = 0
        if quiet or mt:
            return
        self.size = size
        # sys.stdout.write('\r')
        # sys.stdout.write("[%s]" % (" " *  self.size))
        # sys.stdout.flush()
        # sys.stdout.write("\b" * (self.size+1))

    def Update(self):
        if quiet or mt:
            return
        self.it += 1
        sys.stdout.write("\r")
        sys.stdout.write(
            "%d/%d %d%%" % (self.it, self.size, (self.it / self.size) * 100)
        )
        sys.stdout.flush()

    def End(self):
        if quiet or mt:
            return
        sys.stdout.write("\n")
        sys.stdout.flush()
        self.it = 0


def RequestSend(url, headers=None, cookies=None):
    if not is_safe_url(url):
        print(f"Blocked unsafe or unsupported URL: {url}")
        return None

    # Rate limiting: Be a good citizen to target servers
    time.sleep(0.5)

    if headers is None:
        response = requests.get(url)
    else:
        response = requests.get(url, headers=headers, cookies=cookies)
    return response


def RequestPage(url, headers=None):
    response = RequestSend(url, headers)
    attempts = 0
    # print(response.url)
    while response.status_code != 200 and attempts < 4:
        time.sleep(2)
        response = RequestSend(url, headers)
        attempts += 1
    if attempts >= 4:
        print(
            "Server returned status code "
            + str(response.status_code)
            + " for page: "
            + url
        )
        return None
    return response


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


def GetChyoaSession(password):
    global chyoa_session

    user = chyoa_name

    if not user or not password:
        return

    chyoa_session = requests.Session()
    response = chyoa_session.post(
        "https://chyoa.com/auth/login",
        data={"username": user, "password": password},
        headers=default_headers,
    )

    # Check if login was successful
    # Chyoa typically redirects or returns a specific cookie/body on success.
    # We check for the session cookie or status code.
    if (
        response.status_code != 200
        or "logged-in" not in response.text.lower()
        and "logout" not in response.text.lower()
    ):
        chyoa_session = None
        raise AuthenticationError(
            "Failed to log in to Chyoa. Please check your credentials."
        )


def RequestPageChyoa(url, headers=None):
    global chyoa_session
    if chyoa_session is None:
        response = RequestSend(url, headers)
    else:
        response = chyoa_session.get(url, headers=headers)
    attempts = 0
    # print(response.url)
    while response.status_code != 200 and attempts < 4:
        time.sleep(2)
        if chyoa_session is None:
            response = RequestSend(url, headers)
        else:
            response = chyoa_session.get(url, headers=headers)
        attempts += 1
    if attempts >= 4:
        print(
            "Server returned status code "
            + str(response.status_code)
            + " for page: "
            + url
        )
        return None
    return response
