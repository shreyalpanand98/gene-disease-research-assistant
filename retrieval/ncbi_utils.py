
import time
import requests

last_request_time = 0


def ncbi_get(url, params):
    global last_request_time

    for attempt in range(3):

        # Maintain a gap between API requests
        elapsed = time.monotonic() - last_request_time

        if elapsed < 0.4:
            time.sleep(0.4 - elapsed)

        last_request_time = time.monotonic()

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        # Retry when NCBI temporarily rejects the request
        if response.status_code in (429, 500, 502, 503, 504):
            if attempt == 2:
                response.raise_for_status()

            wait_time = 2 ** (attempt + 1)
            print(f"NCBI API error. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            continue

        response.raise_for_status()
        return response
