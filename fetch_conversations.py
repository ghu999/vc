import json
import requests
import time


def make_request(url, api_key, suffix=None):
    """
    Makes a request to Fora API

    Args:
        url (String): url that is being requested
        api_key (String): Fora API key that is in apikey.py
        suffix (String): suffix to add to end of url if needed

    Returns:
        response (Response): response object based on request
    """
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer " + api_key,
    }
    while True:
        print(f"Requesting {url}" + (f" {suffix}" if suffix else ""))
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            print("Hit rate limit. Sleeping for 10 seconds...")
            time.sleep(10)
            continue
        response.raise_for_status()
        break
    return response


def main(type_request, highlight_id, api_key, output_directory):
    """
    Makes an API request to Fora, retrieves the .json and mp3 file of the
    highlight/converation, and returns both paths

    Args:
        type_request (String): request either a highlight or conversation
        (add more later)
        highlight_id (String): ID of highlight (last number in URL)
        api_key (String): Fora API Key used to connect
        output_directory (String): directory that the .json and .mp3
        files should be saved under

    Returns:
        .json path (String), .mp3 path (String): 
        paths of .json and .mp3 files, respectively
    """
    match (type_request):
        case "highlights":
            highlight = make_request(
                f"https://api.fora.io/v1/{type_request}/{highlight_id}",
                api_key,
            ).json()
            (output_directory / f"conversation-{highlight_id}.json").write_text(
                        json.dumps(highlight, indent=4, sort_keys=True),
                    )
            audio = make_request(
                f"https://api.fora.io/v1/{type_request}/{highlight_id}/audio",
                api_key,
            )
            with open(output_directory / f"highlight-{highlight_id}.mp3", "wb") as output_file:
                for chunk in audio:
                    output_file.write(chunk)
            return (output_directory / f"conversation-{highlight_id}.json"), (output_directory / f"highlight-{highlight_id}.mp3")
        case "conversations":
            page = 1
            last_page = 1
            total = 0
            index = 1
            while page <= last_page:
                url = f"https://api.fora.io/v1/conversations?page={page}"
                response = make_request(url, api_key)
                last_page = json.loads(response.headers["X-Pagination"])["last_page"]
                total = json.loads(response.headers["X-Pagination"])["total"]
                for conversation in response.json():
                    conversation_id = conversation["id"]
                    conversation = make_request(
                        f"https://api.fora.io/v1/highlights/{conversation_id}",
                        api_key,
                        suffix=f"({index} / {total})",
                    ).json()
                    (output_directory / f"conversation-{conversation_id}.json").write_text(
                        json.dumps(conversation, indent=4, sort_keys=True),
                    )
                    index += 1
                page += 1
        case _:
            return
