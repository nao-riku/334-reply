import sys
import requests
import os
import json
from requests_oauthlib import OAuth1Session
import time
import datetime
import traceback

consumer_key = os.environ['CK']
consumer_secret = os.environ['CS']
access_token = os.environ['AT']
access_token_secret = os.environ['AS']
bearer_token = os.environ['BT']

oath = OAuth1Session(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

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
    rules = [{"value":"@Rank334 -is:retweet"}]
    payload = {"add": rules}
    response = requests.post("https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth, json=payload)
    if response.status_code != 201:
        raise Exception("Cannot add rules (HTTP {}): {}".format(response.status_code, response.text))
    #print(json.dumps(response.json()))
	
def TweetId2Time(id):
    epoch = ((id >> 22) + 1288834974657) / 1000.0
    d = datetime.datetime.fromtimestamp(epoch)
    d = d.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
    stringTime = ""
    stringTime += '{0:02d}'.format(d.hour)
    stringTime += ':'
    stringTime += '{0:02d}'.format(d.minute)
    stringTime += ':'
    stringTime += '{0:02d}'.format(d.second)
    stringTime += '.'
    stringTime += '{0:03d}'.format(int(d.microsecond / 1000))
    return stringTime

def get_stream(headers):
    global oath
    run = 1
    start = time.time()
    while run:
        try:
            with requests.get("https://api.twitter.com/2/tweets/search/stream?tweet.fields=referenced_tweets", auth=bearer_oauth, stream=True) as response:
                if response.status_code != 200:
                    raise Exception("Cannot get stream (HTTP {}): {}".format(response.status_code, response.text))
                for response_line in response.iter_lines():
                    if response_line:
                        json_response = json.loads(response_line)
                        tweet_text = json_response["data"]["text"]
                        if "@Rank334" in tweet_text or "@rank334" in tweet_text:
                            reply_id = json_response["data"]["id"]
                            rep_text = ""
						
                            if 'referenced_tweets' in json_response["data"]:
                                if json_response["data"]['referenced_tweets'][0]["type"] == "retweeted":
                                    continue
                                else:
                                    tweet_id = json_response["data"]['referenced_tweets'][0]["id"]
                                    rep_text = "ツイート時刻: " + TweetId2Time(int(tweet_id))
                            else:
                                rep_text = "ツイート時刻: " + TweetId2Time(int(reply_id)) + "\n\n順位: /"
							
                            print(rep_text)
                            params = {"text": rep_text, "in_reply_to_status_id": reply_id}
                            response = oath.post("https://api.twitter.com/2/tweets", json = params)
							
                            if time.time() - start > 40:
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
