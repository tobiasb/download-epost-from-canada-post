# Canada Post ePost downloader

Canada Post is shutting down their ePost offering. Unfortunately they don't have a way to bulk download all ePost already received. This script downloads all documents to your local machine one by one. To be able to make authenticated requests, you need to provide your ePost cookie.

1. Open the developer tools of your favorite browser 
2. Log in to https://www.canadapost-postescanada.ca/inbox/en#!/inbox
3. Open the request to https://www.canadapost-postescanada.ca/inbox/rs/mailitem and get the value of the `Cookie` request header

Run `python download-epost.py <cookie value>` or `python download-epost.py <cookie value> <dest>`.

You can run the script multiple times, it will only download files it hasn't downloaded already.