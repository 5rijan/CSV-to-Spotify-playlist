from dotenv import load_dotenv
import os
import base64
import requests
import json
import csv
import logging


load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = CLIENT_ID + ":" + CLIENT_SECRET
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}

    try:
        result = requests.post(url, headers=headers, data=data)
        result.raise_for_status()  # Raise an HTTPError for bad responses
        json_result = result.json()
        token = json_result.get("access_token")
        if token:
            return token
        else:
            print("Token not found in response:", json_result)
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error during token request: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Request Exception during token request: {err}")

    return None

# Attempt to get a new token
new_token = get_token()

if new_token:
    # Update the global token variable
    token = new_token
    print("Successfully obtained a new token.")
else:
    print("Failed to obtain a new token.")

# Function to get user authorization and return access token
def get_user_token(client_id, client_secret, redirect_uri):
    authorization_base_url = "https://accounts.spotify.com/authorize"
    token_url = "https://accounts.spotify.com/api/token"
    scope = "playlist-modify-public playlist-modify-private"  
    state = "123" 

    # Redirect the user to the Spotify Accounts service for authorization
    auth_url = f"{authorization_base_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}"

    print(f"Please go to this URL and authorize access: {auth_url}")
    authorization_code = input("Enter the authorization code from the redirect URI: ")

    # Use the authorization code to request an access token
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8"),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_uri
    }

    try:
        result = requests.post(token_url, headers=headers, data=data)
        result.raise_for_status()
        json_result = result.json()
        user_token = json_result.get("access_token")
        if user_token:
            return user_token
        else:
            print("User Token not found in response:", json_result)
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error during user token request: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Request Exception during user token request: {err}")

    return None

# Update the global token variable with the user token
# *authorization code in the google url itself copy paste from there*
redirect_uri = "https://www.google.co.in/" 
user_token = get_user_token(CLIENT_ID, CLIENT_SECRET, redirect_uri)

if user_token:
    token = user_token
    print("Successfully obtained user token.")
else:
    print("Failed to obtain user token.")

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def get_user_detials(token):
    url = "https://api.spotify.com/v1/me"
    headers = get_auth_header(token)
    result = requests.get(url, headers=headers)
    json_result = result.json()
    return json_result

def create_playlist(token, title):
    my_user_id = get_user_detials(token)["id"]
    url = f"https://api.spotify.com/v1/users/{my_user_id}/playlists"
    headers = get_auth_header(token)
    headers["Content-Type"] = "application/json"
    data = {"name": title}
    data_json = json.dumps(data)
    result = requests.post(url, headers=headers, data=data_json)
    json_result = result.json()
    return json_result

def search_the_song(token, artist_name, song_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={song_name} {artist_name}&type=track&limit=3"

    query_url = url + query
    result = requests.get(query_url, headers=headers)
    json_result = json.loads(result.content)

    # Check if the song was found
    if json_result['tracks']['items']:
        return json_result['tracks']['items'][0]
    else:
        print(f"Song not found: {song_name} by {artist_name}")
        return None

def add_tracks_to_playlist(token, playlist_id, track_ids):
    playlist_id = playlist_id
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_header(token)
    headers["Content-Type"] = "application/json"
    data = {"uris": track_ids}
    data_json = json.dumps(data)
    result = requests.post(url, headers=headers, data=data_json)
    json_result = result.json()
    return json_result


logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
def main():
    filepath = "csv files/world/world-22-01-2024.csv"
    title, _ = os.path.splitext(os.path.basename(filepath))
    print(f'Title: {title}')
    playlist = create_playlist(token, title)
    playlist_id = playlist["id"]
    with open(filepath, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the title
        next(csv_reader)  # Skip the date
        next(csv_reader)  # Skip the header
        total_songs = sum(1 for row in csv.reader(open(filepath))) - 3  # Subtract 3 for the skipped rows
        processed_songs = 0

        for row in csv_reader:
            artist_name = row[1]
            track_name = row[2]
            track = search_the_song(token, artist_name, track_name)
            if track:
                track_id = track["uri"]
                add_tracks_to_playlist(token, playlist_id, [track_id])
            else:
                logging.warning(f'This track not found hence not being added to playlist: {track_name} by {artist_name}')
            processed_songs += 1
            print(f'Adding {track_name} by {artist_name} ({processed_songs}/{total_songs} {processed_songs/total_songs*100:.2f}%)')
            continue


if __name__ == "__main__":
    main()
