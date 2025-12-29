# Ebook-Publisher v3.4.0

A Python tool for converting online stories into portable formats.

## Features

* **Security Hardened:** Secure credential handling, XML injection protection, and path traversal prevention.
* **Format Support:** Plain text (TXT), EPUB, and HTML output.
* **Automation:** Supports multiple URLs, batch files, and standard input (piping).
* **Multithreading:** Rapidly download multiple stories simultaneously.
* **Site Integration:** Full support for scraping complex sites like Chyoa and Nhentai, including image support and login capabilities.

## Installation

Ebook-Publisher requires Python 3.

1. Clone the repository: `git clone https://github.com/theslavicbear/Ebook-Publisher.git`
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script and provide one or more URLs, a text file containing URLs, or pipe URLs directly to the script.

```bash
python Ebook-Publisher.py [URL/FILE] [OPTIONS]
```

### Credentials (Chyoa)

For stories requiring login, you can provide credentials securely:

* **Interactive Prompt:** Provide `--usr your_username` and you will be prompted for your password securely.
* **Environment Variables:** Set `CHYOA_USER` and `CHYOA_PASSWORD` in your environment.

### Options

```
  -o, --output-type {txt,epub,html}  The file type(s) you want (can be used multiple times)
  -d, --directory DIRECTORY           Directory to place output files
  -q, --quiet                         Turns off most terminal output
  -t                                  Turns on multithreading mode
  -i, --insert-images                 Downloads images for Chyoa/Nhentai
  -n, --no-duplicates                 Skips stories already downloaded
  -s, --css CSS                       CSS string or .css file for formatting
  --usr USR                           Chyoa username to log in with
  --chyoa-update                      Only download if the story has been updated since the last download
  --chyoa-force-forwards               Force Chyoa stories to be scraped from the beginning
  --eol EOL                           Custom end-of-line character for TXT output (e.g., '\n')
```

### Examples

```bash
# Basic usage
python Ebook-Publisher.py https://chyoa.com/story/example -o epub

# Batch processing from a file
python Ebook-Publisher.py urls.txt -o epub -o html -d ./my_books/

# Multithreaded download with images
python Ebook-Publisher.py urls.txt -t -i -o epub

# Secure login
python Ebook-Publisher.py https://chyoa.com/story/private --usr MyUser -o epub
```

## Currently supported sites

* **chyoa.com**
* **nhentai.net**
* **literotica.com**
* **fanfiction.net**
* **fictionpress.com**
* **wattpad.com**
* **classicreader.com**

## Security & Privacy

* **Credential Safety:** Passwords are never echoed to the screen or stored in history when using the interactive prompt or environment variables.
* **Data Integrity:** EPUB generation uses a secure XML builder to prevent injection attacks.
* **Path Safety:** Output filenames are sanitized to prevent directory traversal.
* **Modern Identity:** Uses a modern User-Agent to reduce bot detection and IP flagging.

## Contributing

Ebook-Publisher is a pet project. I welcome criticism, requests for improvement, and bug reports via Issues.