# Image OCR using google docs, output to srt file

refactor the code more properly

## How to use

Create new google cloud project and download `credentials.json` file: see https://developers.google.com/drive/api/quickstart/python

put credentials.json file beside main.py

Install the Google Client Library: `pip install -r requirements.txt`

Export images fro hard-subbed video: https://sourceforge.net/projects/videosubfinder/

Run `python main.py` and login with google account (only for first time), it creates a new file `token.json`

Wait until it complete processing evey image.

Code is based on https://tanaikech.github.io/2017/05/02/ocr-using-google-drive-api/