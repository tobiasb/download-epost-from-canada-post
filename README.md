# Canada Post epost downloader

Canada Post is shutting down their epost service at the end of 2022. Unfortunately they don't have a way to bulk download all epost already received. This script downloads all documents to your local machine one by one. To be able to make an authenticated requests, you need to provide your epost cookie.

Requirements: `Python` and Python package `requests` installed.

1. Open the developer tools of your favorite browser 
2. Log in to https://www.canadapost-postescanada.ca/inbox/en#!/inbox
3. Open the request to https://www.canadapost-postescanada.ca/inbox/rs/mailitem and get the value of the `Cookie` request header    
![Network Inspect](https://github.com/Jakesta13/download-epost-from-canada-post/blob/main/Inspect%20Network.PNG?raw=true)    
![Cookie Example](https://github.com/Jakesta13/download-epost-from-canada-post/blob/main/Epost%20Cookie%20Example.png?raw=true)    

Run `python download-epost.py "'<cookie value>'"` or `python download-epost.py "'<cookie value>'" <dest>`. Enclose your cookie value in double and single quotes as it can contain characters that'd be interpreted by your shell.

You can run the script multiple times, it will only download files it hasn't downloaded already.