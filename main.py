import os
import io
import srt
from glob import glob
from tqdm import tqdm
from datetime import timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


SCOPES = ["https://www.googleapis.com/auth/drive"]
def get_credentials(token_file, credentials_file):
	if os.path.exists(token_file):
		creds = Credentials.from_authorized_user_file(token_file, SCOPES)
	else:
		creds = None
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
			creds = flow.run_local_server(port=0)
		with open(token_file, "w") as token:
			token.write(creds.to_json())
		print("Storing credentials to", token_file)
	return creds


CREDENTIALS = get_credentials("token.json", "credentials.json")
SERVICE = discovery.build(serviceName="drive", version="v3", credentials=CREDENTIALS)
MIME = "application/vnd.google-apps.document"

IMAGES_DIR = "RGBImages"
RAW_TEXTS_DIR = "TXTResults"
images = glob("*.jpeg", root_dir=IMAGES_DIR)
if not os.path.isdir(IMAGES_DIR) or len(images) == 0: raise ValueError("empty image folder")
if not os.path.isdir(RAW_TEXTS_DIR): os.mkdir(RAW_TEXTS_DIR)


def get_text_from_ocr(image: srt) -> str:
	"""use google docs OCR"""
	imgfile = os.path.join(IMAGES_DIR, image)
	imgname = os.path.splitext(image)[0]
	raw_txtfile = os.path.join(RAW_TEXTS_DIR, imgname+".txt")

	res = SERVICE.files().create(
		body={"name": imgfile, "mimeType": MIME}, fields="id",
		media_body=MediaFileUpload(imgfile, mimetype=MIME, resumable=True)
	).execute()
	file_id = res.get("id")

	downloader = MediaIoBaseDownload(
		io.FileIO(raw_txtfile, "wb"),
		SERVICE.files().export_media(fileId=file_id, mimeType="text/plain")
	)
	done = False
	while not done:
		_, done = downloader.next_chunk()
	SERVICE.files().delete(fileId=file_id).execute()

	with open(raw_txtfile, "r", encoding="utf-8") as raw_text_file:
		text_content = raw_text_file.read().split("\n")
	return "".join(text_content[2:])


def get_timestamp_from_filename(image: srt) -> tuple[timedelta, timedelta]:
	"""get start & end timestamp from image file name, which comes from VideoSubFinder"""
	imgname = os.path.splitext(image)[0]

	tmp_start = imgname.split("_")
	start_hour  = int(tmp_start[0][:2])
	start_min   = int(tmp_start[1][:2])
	start_sec   = int(tmp_start[2][:2])
	start_micro = int(tmp_start[3][:3])

	tmp_end = imgname.split("__")[1].split("_")
	end_hour  = int(tmp_end[0][:2])
	end_min   = int(tmp_end[1][:2])
	end_sec   = int(tmp_end[2][:2])
	end_micro = int(tmp_end[3][:3])

	start_time = timedelta(hours=start_hour, minutes=start_min, seconds=start_sec, microseconds=start_micro)
	end_time   = timedelta(hours=  end_hour, minutes=  end_min, seconds=  end_sec, microseconds=  end_micro)
	return start_time, end_time


#################################### main #####################################

OUTPUT_FILE = "subtitle_output.srt"
subs = []

for line, image in enumerate(tqdm(images, unit="image"), start=1):
	txt = get_text_from_ocr(image)
	start_time, end_time = get_timestamp_from_filename(image)
	subs.append(srt.Subtitle(index=line, start=start_time, end=end_time, content=txt))

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
	f.write(srt.compose(srt.sort_and_reindex(subs)))  # order get messed up on linux