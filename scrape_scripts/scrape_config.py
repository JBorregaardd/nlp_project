START_URL = "https://www.sundhed.dk/borger/patienthaandbogen/infektioner/sygdomme/virusinfektioner/"

ALLOWED_PREFIX = "https://www.sundhed.dk/borger/patienthaandbogen/"
BRANCH_PREFIX = "https://www.sundhed.dk/borger/patienthaandbogen/infektioner/sygdomme/virusinfektioner/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "da-DK,da;q=0.9,en;q=0.8",
}

REQUEST_DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 15