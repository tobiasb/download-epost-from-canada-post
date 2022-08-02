# Canada Post epost downloader

Canada Post is shutting down their epost service at the end of 2022. Unfortunately they don't have a way to bulk download all epost already received. This script downloads all documents to your local machine one by one. To be able to make an authenticated requests, you need to provide your epost cookie.

Requirements: `Python` and Python package `requests` installed.

1. Open the developer tools of your favorite browser
2. Log in to https://www.canadapost-postescanada.ca/inbox/en#!/inbox
3. Open the request to https://www.canadapost-postescanada.ca/inbox/rs/mailitem and get the value of the `Cookie` request header
4. [*OPTIONAL*] Open the epost folder that you'd like to download and get the folder id from the end of the folder URL (i.e. `1234567` from the folder URL https://www.canadapost-postescanada.ca/inbox/en#!/folder/details/**1234567**)

Run `python download-epost.py --cookies '<COOKIE_VALUES>'`. Enclose your cookie values in single quotes as it can contain characters that could be interpreted by your shell.

Optionally, you can include the `--dest '<DEST>'` option to specify the directory to download the documents into and the `--folder <FOLDER_ID>` option to specify the epost folder to download (see step 4 above).

You can run the script multiple times, it will only download files it hasn't downloaded already.