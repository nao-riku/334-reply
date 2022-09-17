import sys
import requests
import os
import json
from requests_oauthlib import OAuth1Session
import time
import traceback
import tweepy

consumer_key = os.environ['CK']
consumer_secret = os.environ['CS']
access_token = os.environ['AT']
access_token_secret = os.environ['AS']
bearer_token = os.environ['BT']

Client = tweepy.Client(bearer_token, consumer_key, consumer_secret, access_token, access_token_secret)

def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r

def get_rules():
    response = requests.get("https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth)
    if response.status_code != 200:
        raise Exception("Cannot get rules (HTTP {}): {}".format(response.status_code, response.text))
    #print(json.dumps(response.json()))
    return response.json()

def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None
    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post("https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth, json=payload)
    if response.status_code != 200:
        raise Exception("Cannot delete rules (HTTP {}): {}".format(response.status_code, response.text))
    #print(json.dumps(response.json()))

def set_rules(delete):
    rules = [{"value":"@Rank334"}]
    payload = {"add": rules}
    response = requests.post("https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth, json=payload)
    if response.status_code != 201:
        raise Exception("Cannot add rules (HTTP {}): {}".format(response.status_code, response.text))
    #print(json.dumps(response.json()))

def get_stream(headers):
    run = 1
    start = time.time()
    while run:
        try:
            with requests.get("https://api.twitter.com/2/tweets/search/stream", auth=bearer_oauth, stream=True) as response:
                if response.status_code != 200:
                    raise Exception("Cannot get stream (HTTP {}): {}".format(response.status_code, response.text))
                for response_line in response.iter_lines():
                    if response_line:
                        json_response = json.loads(response_line)
                        tweet_id = json_response["data"]["id"] #ツイートID
                        tweet_text=json_response["data"]["text"] #相手の送ってきた内容
			    if "@Rank334" in tweet_text or "@rank334" in tweet_text:
                    print(tweet_id)
			        Client.create_tweet(text="reply test", in_reply_to_tweet_id =tweet_id)
                if time.time() - start > 20:
                    sys.exit()


        except ChunkedEncodingError as chunkError:
            print(traceback.format_exc())
            time.sleep(6)
            continue
        
        except ConnectionError as e:
            print(traceback.format_exc())
            run+=1
            if run <10:
                time.sleep(6)
                print("再接続します",run+"回目")
                continue
            else:
                run=0
        except Exception as e:
            # some other error occurred.. stop the loop
            print("Stopping loop because of un-handled error")
            print(traceback.format_exc())
            run = 0
	    
class ChunkedEncodingError(Exception):
    pass

def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete)
    get_stream(set)

 
if __name__ == "__main__":
    main()
