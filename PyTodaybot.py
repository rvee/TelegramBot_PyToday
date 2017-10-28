import requests
import json
import time
from datetime import datetime, timedelta
from pytz import timezone
from pytz import utc
import re
from os.path import expanduser


# Store and your Bot token in your home directory -> ~/.tokens/telegram_bot
home = expanduser("~")
token_file = str(home) + '/.tokens/telegram_bot'
with open(token_file) as f:
    token = f.readline().strip()


tg_url = 'https://api.telegram.org/bot{token}/'.format(**locals())


def get_url(url):
    response = requests.get(url)
    return json.loads(response.text)


def get_updates(offset=None):
    if offset:
        return get_url(tg_url+'getUpdates?timeout=100'+"&offset={offset}".format(**locals()))
    return get_url(tg_url+'getUpdates?timeout=100')


def send_updates(chat_id, text):
    return get_url(tg_url+'sendMessage?chat_id={chat_id}&text={text}'.format(**locals()))


def send_inline(answer):
    return requests.post(url=tg_url + 'answerInlineQuery', params=answer)


def last_update_id(updates):
    update_ids = []
    for update in updates['result']:
        update_ids.append(int(update['update_id']))
    return max(update_ids)


def echo_all(updates):
    for update in updates['result']:
        try:
            chat_id = update['message']['chat']['id']
            text = update['message']['text']
            from_id = update['message']['from']['username']
            # print('Received from ' + from_id + ' > ' + text)
            send_updates(chat_id, text)
            print('Chat Echoed ' + from_id + ' > ' + text)
        except Exception as e:
            print(e)


def get_hydpy_meetup(chat_id):
    response = requests.get('https://api.meetup.com/2/events?offset=0&format=json&limited_events=False'
                            '&group_urlname=Hyderabad-Python-Meetup-Group&photo-host=public&page=20&fields=&order=time'
                            '&desc=false&status=upcoming&sig_id=8101615&sig=47907134e718c42220aa2e8a7de154be8757318b')
    parsed_json = json.loads(response.text)
    if len(parsed_json['results']) > 0:
        send_updates(chat_id, 'I noticed there are ' + str(len(parsed_json['results'])) + ' Meetups')
        for i in range(len(parsed_json['results'])):
            utc_dt = utc.localize(datetime.utcfromtimestamp(parsed_json['results'][i]['time']//1000))
            ist_dt = utc_dt.astimezone(timezone('Asia/Kolkata'))
            try:
                venue = parsed_json['results'][i]['venue']['name']
            except Exception as e:
                print(e)
                venue = 'Location unavailable'
            text = ('Meetup Name: ' + parsed_json['results'][i]['name'] + '\n' +
                    'Location: ' + venue + '\n' +
                    'Time: ' + str(ist_dt.strftime('%I:%M %p, %b %d,%Y (%Z)')) + '\n' +
                    'RSVP Here: ' + parsed_json['results'][i]['event_url'])
            send_updates(chat_id, text)
    else:
        send_updates(chat_id, 'There are no new Meetups scheduled :(')


def get_inline_hydpy_meetup():
    response = requests.get('https://api.meetup.com/2/events?offset=0&format=json&limited_events=False'
                            '&group_urlname=Hyderabad-Python-Meetup-Group&photo-host=public&page=20&fields=&order=time'
                            '&desc=false&status=upcoming&sig_id=8101615&sig=47907134e718c42220aa2e8a7de154be8757318b')
    parsed_json = json.loads(response.text)
    meetup_details = []
    if len(parsed_json['results']) > 0:
        for i in range(len(parsed_json['results'])):
            utc_dt = utc.localize(datetime.utcfromtimestamp(parsed_json['results'][i]['time']//1000))
            ist_dt = utc_dt.astimezone(timezone('Asia/Kolkata'))
            try:
                venue = parsed_json['results'][i]['venue']['name']
            except Exception as e:
                print(e)
                venue = 'Location unavailable'
            text = ('Meetup Name: ' + parsed_json['results'][i]['name'] + '\n' +
                    'Location: ' + venue + '\n' +
                    'Time: ' + str(ist_dt.strftime('%I:%M %p, %b %d,%Y (%Z)')) + '\n' +
                    'RSVP Here: ' + parsed_json['results'][i]['event_url'])
            meetup_details.append({'meetname': parsed_json['results'][i]['name'],
                                   'location': venue,
                                   'time': str(ist_dt.strftime('%I:%M %p, %b %d,%Y (%Z)')),
                                   'url': parsed_json['results'][i]['event_url'],
                                   'text': text})
    return meetup_details


def prt_recd_from(data, method, query):
    try:
        from_id = data['from']['username']
        if method == 'inline_query':
            print('Inline Query Received from ' + from_id + ' > ' + query)
        elif method == 'message':
            print('Chat Received from ' + from_id + ' > ' + query)
        return from_id
    except Exception as e:
        print(e)
    return


def prt_sent_to(from_id, method, action):
    try:
        if from_id:
            if method == 'inline_query':
                print('Inline Query answered to ' + from_id + ' > ' + action)
            elif method == 'message':
                print('Chat Replied to ' + from_id + ' > ' + action)
    except Exception as e:
        print(e)
    return


def commander(updates):
    for update in updates['result']:
        if 'inline_query' in update:
            inline_query = update['inline_query']
            inline_query_id = inline_query['id']
            query = inline_query['query']
            from_id = prt_recd_from(inline_query, 'inline_query', query)
            if re.search('hydpy', query, re.IGNORECASE):
                meetup_list = get_inline_hydpy_meetup()
                results = []
                for u_id, meetup in enumerate(meetup_list):
                    results.append({'type': 'article',
                                    'id': u_id,
                                    'title': meetup['meetname'],
                                    'parse_mode': 'Markdown',
                                    'message_text': meetup['text'],
                                    'description': meetup['url']})
                answer = {'inline_query_id': inline_query_id, 'results': json.dumps(results), 'cache_time': '30'}
                send_inline(answer)
                prt_sent_to(from_id, 'inline_query', 'HydPy Meetup Details')
        else:
            try:
                message = update['message']
                chat_id = message['chat']['id']
                query = message['text']
                from_id = prt_recd_from(message, 'message', query)
                if re.search('hydpy', query, re.IGNORECASE):
                    get_hydpy_meetup(chat_id)
                    prt_sent_to(from_id, 'message', 'HydPy Meetup Details')
                else:
                    echo_all(updates)
            except Exception as e:
                print(e)


def main():
    offset = None
    while True:
        try:
            all_updates_json = get_updates(offset)
            if len(all_updates_json['result']) > 0:
                offset = last_update_id(all_updates_json) + 1
                commander(all_updates_json)
        except Exception as e:
            print(e)
        time.sleep(0.4)


if __name__ == '__main__':
    main()

# if len(parsed_content['result'])>0:
#     for i in parsed_content['result']:
#         if parsed_content['result'][0]['message']['from']['username'] not in temp_user_list:
#             temp_user_list.append(parsed_content['result'][0]['message']['from']['username'])
#             first_name = parsed_content['result'][0]['message']['from']['first_name']
#             send_text='Hello {first_name}'.format(**locals())
#             send_updates(parsed_content['result'][0]['message']['chat']['id'],send_text)
#         send_updates(parsed_content['result'][0]['message']['chat']['id'],'Howdy!')
