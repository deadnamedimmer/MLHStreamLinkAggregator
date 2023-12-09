from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from twitch_chat_irc import twitch_chat_irc
import requests
from decouple import config
from urlextract import URLExtract

extractor = URLExtract()

CLIENT_SECRET = config('SECRET')

connection = twitch_chat_irc.TwitchChatIRC()

def getStreamInfo():
    client_id = "u8i39z41hzuearl5nimvc6gul4f778"
    url = 'https://id.twitch.tv/oauth2/token'
    myobj = {'client_id': client_id, 'client_secret': CLIENT_SECRET, 'grant_type': 'client_credentials'}

    token = requests.post(url, json = myobj)
    access_token = token.json()['access_token']
    token_type = token.json()['token_type']

    stream_info = requests.get('https://api.twitch.tv/helix/channels?broadcaster_id=79176881', headers={'Authorization': 'Bearer ' + access_token, 'Client-Id': client_id})
    stream_title = stream_info.json()['data'][0]['title']
    return(stream_title)

def writeToSheets(link, stream_title, timestamp):
    spreadsheet_id = "1fveoPgbPLdGOqlYjtpvli9QDu6oFpLMLXPauBtrnGts"

    credentials = service_account.Credentials.from_service_account_file("mlhstreamlinkaggregator-dde815d11b36.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])

    date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
    time = datetime.utcfromtimestamp(timestamp).strftime('%H:%M:%S')

    try:
        service = build("sheets", "v4", credentials=credentials)
        values = [
            [stream_title, date, time, link],
        ]
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range="Sheet1!A1:D",
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updatedCells')} cells updated.")
    except HttpError as error:
        print(f"An error occurred: {error}")

def do_something(message):
    if message['user-type'] == 'mod' or message['display-name'] == 'MLH':
        chat_message = message['message']
        print(chat_message)
        if extractor.has_urls(chat_message):
            print('Found link')
            timestamp = int(message['tmi-sent-ts'][:-3])
            stream_title = getStreamInfo()
            urls = extractor.find_urls(chat_message)
            for link in urls:
                writeToSheets(link, stream_title, timestamp)
                print('Wrote ' + link + 'to database')


connection.listen('mlh', on_message=do_something)