from argparse import ArgumentParser, ArgumentTypeError
from os import path
from re import findall
from requests import Session, adapters, get
from requests.adapters import HTTPAdapter, Retry

class EpostDownloadClient(object):
    """
    Canada Post epost download client.
    """
    # tracks total number of documents downloaded successfully
    downloaded = 0

    # maximum page size for pagination
    page_size = 50

    # tracks total number of documents processed successfully
    processed = 0
    
    # tracks download results for each item
    results = []

    # tracks total number of documents
    total = 0

    def __init__(self, cookies, dest):
        """
        Initialize epost client class object with default values.
        """

        # valid epost session cookies
        self.cookies = cookies

        # destination for downloaded documents
        self.dest = dest

        # session request retry configuration
        # default to a maximum of five retries with backoff factor of 1 second
        # and force retry on 502, 503, and 504 HTTP status errors
        self.retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])

    def __enter__(self):
        """
        Setup HTTP session with retry and header configuration.
        """

        # setup new session object, will be destroyed on exit
        self.session = Session()

        # configure maximum retries
        self.session.mount("https://", HTTPAdapter(max_retries=self.retries))

        # define Cookie and CSRF headers
        self.session.headers.update({
            "Cookie": self.cookies,
            "csrf": self._get_sso_token()
        })

        # setup result values or reset from any previous executions
        self._prepare()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close HTTP session on exit.
        """
        
        # close session connection
        self.session.close()

    def _get_sso_token(self):
        """
        Attempt to return a valid SSO token for the configured cookie session.
        """

        # request inbox to obtain sso token values without configured session retries
        response = get("https://www.canadapost-postescanada.ca/inbox/en", headers={
            "Cookie": self.cookies
        })

        # parse all sso token values where content value is provided
        sso_tokens = findall('"sso-token" content="([a-z0-9\-]*)"', response.text)
        potential_sso_tokens = [token for token in sso_tokens if token]

        # validate that atleast one SSO token was found
        if not potential_sso_tokens:
            raise ValueError("Failed getting a SSO token. Are you sure you provided your up to date cookies? 🤔")

        # return first valid sso token value
        return potential_sso_tokens[0]

    def _prepare(self):
        """
        Reset result values to clear any previous execution values.
        """
        self.downloaded = 0
        self.processed = 0
        self.results = []
        self.total = 0

    def _to_result(self, folder_id, item_id, item_desc, status):
        """
        Append provided folder item details and status to list of results.
        """
        self.results.append({
            "folder": folder_id,
            "item": item_id,
            "desc": item_desc,
            "status": status
        })

    def download(self, folder_id):
        """
        Download all documents within the provided epost folder to the configured destination.
        """

        # validate that a request session is configured
        if not self.session:
            raise ValueError("Session must be configured first!")

        # track first passthrough for total counts
        first_time = True

        # track page offset for pagination
        offset = 0

        # loop until all pages have been processed
        while True:

            # resolve epost API endpoint for folder items
            folder_items_endpoint = f"https://www.canadapost-postescanada.ca/inbox/rs/mailitem?folderId={folder_id}&sortField=1&order=D&offset={offset}&limit={self.page_size}"

            # request folder items' detail using configured session
            response = self.session.get(folder_items_endpoint)

            # raise error if response HTTP status code is not 200 (OK)
            if response.status_code != 200:
                raise ValueError(f"Request to {folder_items_endpoint} failed with HTTP {response.status_code} 🔥")

            # raise error if response content length is none
            if "content-length" in response.headers and response.headers["content-length"] == "0":
                raise ValueError("Failed getting a response. Are you sure you provided your up to date cookies? 🤔")

            # parse response text as a JSON formatted string
            data = response.json()

            # if first passthrough, add total folder items to num total
            if first_time:
                self.total += data["numTotal"] if "numTotal" in data else 0
                first_time = False

            # skip if no items in the folder
            if len(data["mailitemInfos"]) == 0:
                break

            # loop through each item in the folder for the current page
            for mail_item in data["mailitemInfos"]:

                # define item id and descrpition details
                item_id = mail_item["mailItemID"]
                item_desc = mail_item["shortDescription"]

                # resolve file name from short description and item id
                # replace any slashes with dashes
                file_name = f'{item_desc}.{item_id}.pdf'.replace("/", "-")

                # resolve download file path location
                file_location = path.join(self.dest, file_name)

                # if file already exists, skip
                if path.exists(file_location):

                    # append already downloaded stutus to list of results
                    self._to_result(folder_id, item_id, item_desc, f"Already downloaded '{file_location}', skipping 💪")

                    # increase item processed count by one
                    self.processed += 1

                    # continue to next item in list
                    continue

                # resolve epost API endpoint for folder item download
                item_download_endpoint = f"https://www.epost.ca/service/displayMailStream.a?importSummaryId={item_id}"

                # download folder item
                response = self.session.get(item_download_endpoint)

                # validate that response status code is 200 (OK)
                if response.status_code != 200:

                    # append error status to results
                    self._to_result(folder_id, item_id, item_desc, f"Downloading '{item_desc}' failed with HTTP '{response.status_code}' 🔥")

                    # continue to next folder item without raising an error
                    continue

                # append success status to results
                self._to_result(folder_id, item_id, item_desc, f"Downloaded '{file_location}' 👍")

                # write response content to download destitation
                with open(file_location, mode="bw") as f:
                    f.write(response.content)

                # increase downloaded and processed counts
                self.downloaded += 1
                self.processed += 1

            # increase page offset by page size to process the next page of the folder
            offset += self.page_size

if __name__ == '__main__':

    parser = ArgumentParser()

    # optional arguments
    parser.add_argument('-d', '--dest', help="destination for downloads (default: '')",
                        metavar="'<DEST>'", type=str, default="")
    parser.add_argument('-f', '--folder', help="epost folder id (default: 0)", 
                        metavar="<FOLDER_ID>", type=int, default=0)

    # create required argument group
    required_args = parser.add_argument_group('required arguments')
    required_args.add_argument('-c', '--cookies', help="epost session cookies",
                               metavar="'<COOKIE_VALUES>'", type=str, required=True)

    # parse arguments and halt if required are not provided
    args = parser.parse_args()

    # print arguments for transparency
    print("Processing epost document download with the following arguments:")
    print("  --cookies : %s" % (args.cookies[:75] + '...') if len(args.cookies) > 78 else args.cookies)
    print("  --dest    : %s" % args.dest)
    print("  --folder  : %s" % ("Inbox (0)" if args.folder == 0 else args.folder))

    # create epost client from arguments
    with EpostDownloadClient(args.cookies, args.dest) as client:

        # download all documents for provided folder
        client.download(args.folder)

        # print all result statuses
        for result in client.results:
            if "status" in result and result["status"]:
                print(result["status"])

        # print total counts
        print(f"Processed {client.processed} of {client.total}! Downloaded {client.downloaded} new documents. 🎉")
