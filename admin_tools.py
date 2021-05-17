import random
import json
import re
from MySQL import MySQL


CLASS_REFEX = r'/(\d+)(\w)\w*/iu'

mysql = MySQL("config.json")

'''expires: once-seen — disappears when user just open it

expires: limited-time — disappears after the specified time is reached
+ expires_at: the date PHP understands (prob. ISO)

Ex.:
{
	"id": 3,
	"expires": "limited-time",
	"msg_text": "Это сообщение должно исчезнуть в 22:46",
	"expires_at": "2021-04-24 22:46"
}

expires: limited-seen — disappears after it is LOADED specified number of times. In fact,
once-seen is limited-seen with expires_at = 1

+ expires_at: just a number of suggested looks. Ex. — look at standart announcements.

any other — needs manual closing. Not recommended because users are too lazy…

Ex.:

{
	"id": 4,
	"msg_text": "This one should be stable"
}

id is needed (simultaneously to be responsible for closing) to be easier to manage the messages.
For ex., you can create message for all the users, than, when it will become redundant, remove all
with this id. That means flexebility in terms of expiring and text for different users.'''

def msg_construct(msg_text, expires=None, expires_at=None, msg_id=None):
    assert msg_id == None or (type(msg_id) == int and msg_id > 0)

    if msg_id is None:
        msg_id = random.randint(1, 1_000_000_00)

    msg = {
        "id": msg_id,
        "msg_text": msg_text
    }

    if expires:
        msg['expires'] = expires

    if expires_at:
        msg['expires_at'] = expires_at

    return msg


def get_msgs_for_person(person_id):
    data_got = mysql.fetch(
        'SELECT msg_data FROM `messages` WHERE `user_id` = ' + str(person_id))
    if data_got == () or data_got[0]['msg_data'] is None:
        return None
    return json.loads(data_got[0]['msg_data'])


def set_msgs_for_person(person_id, msgs):
    try:
        mysql.query("UPDATE netschool.messages SET msg_data = '{}' WHERE `user_id` = {}".format(
            json.dumps(msgs, ensure_ascii=False), person_id))
        return True
    except Exception as err:
        print(err, 'during the query')
        print(json.dumps(msgs, ensure_ascii=False))


def get_persons_id_by(prop, value):
    return [user['id'] for user in users if user[prop] == value]


def is_id_in_msgs(msgs, msg_id):
    global msgs_
    msgs_ = msgs
    return [msg for msg in msgs if msg['id'] == msg_id]


def recipients_from_string(recipients):
    if type(recipients) == str:
        recipients = recipients.lower()
        if re.fullmatch(CLASS_REFEX, recipients):
            recipients = get_persons_id_by('class', recipients)
        elif recipients == 'all':
            recipients = users_ids
        else:
            recipients = get_persons_id_by('name', recipients)
    if type(recipients) == int:
        recipients = [recipients]
    return recipients


def set_msg_for_persons(recipients, constructed_msg, duplicates='LOG'):
    recipients = recipients_from_string(recipients)
    print('Total receivers:', len(recipients))
    counter = 0
    for recipient in recipients:
        msgs = get_msgs_for_person(recipient)
        if msgs is None:
            continue
        if is_id_in_msgs(msgs, constructed_msg['id']):
            if duplicates == 'LOG':
                print(constructed_msg, 'ignored; duplicate')
                continue
            elif duplicates == 'ADD':
                pass
            elif duplicates == 'IGNORE':
                continue
            else:
                raise RuntimeError("Duplicates found")
        msgs.append(constructed_msg)
        if set_msgs_for_person(recipient, msgs):
            counter += 1
    print('Total received:', counter)


def delete_msg_by_id(msg_id, recipients='all'):
    recipients = recipients_from_string(recipients)
    for recipient in recipients:
        msgs = get_msgs_for_person(recipient)
        if not msgs:
            continue

        msgs_to_delete = is_id_in_msgs(msgs, msg_id)

        for msg in msgs_to_delete:
            msgs.remove(msg)
        set_msgs_for_person(recipient, msgs)


users = mysql.fetch("SELECT `id`, `name`, `last_visit`, `class`, `username` FROM `users`")
users_ids = [user['id'] for user in users]
