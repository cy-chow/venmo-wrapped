import utils_venmo as utils
import venmo_api as venmo
import argparse
from collections import defaultdict

# parse command line args
parser = argparse.ArgumentParser(description='Venmo Wrapped')
parser.add_argument('-t', '--token_file', metavar='T', type=str, 
                    help='file containing access token')
parser.add_argument('-u', '--username', metavar='U', type=str, 
                    help='source user to analyze')
parser.add_argument('--anon', action='store_true', help='anonymize usernames')

args = parser.parse_args()

# read access token from file
token_file = args.token_file if args.token_file else utils.DEFAULT_TOKEN_FILE
with open(token_file, 'r') as file:
    access_token = file.read().rstrip()

client = venmo.Client(access_token=access_token)
client_user = client.user.get_my_profile()

if not args.username or args.username == client_user.username:
    # if no username given, use the account associated with client
    test_user = client_user
else:
    # look for input account
    users = client.user.search_for_users(query=args.username, limit=1)
    if len(users) == 0:
        print('Input username not found')
        exit()
    test_user = users[0]

print('\nVenmo Wrapped\n', test_user.username, '(', 
        test_user.first_name, test_user.last_name,')',
        '\n UserId:', test_user.id)

# get user transactions
transactions = utils.get_all_user_transactions(client, test_user.id, utils.DEFAULT_TOTAL_PAGES)
# utils.save_transactions(test_user.id, transactions)

friends = client.user.get_user_friends_list(user_id = test_user.id)
friend_usernames = {f.username : f for f in friends}
stranger_usernames = {}

# anonymize if needed
if args.anon:
    utils.anonymize(friend_usernames)

# check which transactions are available
print()
if client_user.username in friend_usernames:
    print('public transactions and transactions available between friends')
elif not args.username or client_user.username == args.username: 
    print('all transactions')
else:
    print('only public transactions')

print('Total Visible Transactions Made :', len(transactions),'\n')

# if we need more fine grain (directed transactions) later
to_friend = defaultdict(int) # friend was paid
from_friend = defaultdict(int) # friend pays
to_stranger = defaultdict(int)
from_stranger = defaultdict(int)

f_trans = defaultdict(int)
s_trans = defaultdict(int)

for t in transactions:
    # check friends
    if t.actor.username in friend_usernames:
        f_trans[t.actor.username] += 1
        from_friend[t.actor.username] += 1
    elif t.target.username in friend_usernames:
        f_trans[t.target.username] += 1
        to_friend[t.target.username] += 1
    elif t.actor.username != test_user.username:
        # add to strangers if user not yet seen
        if t.actor.username not in stranger_usernames:
            stranger_usernames[t.actor.username] = t.actor
        s_trans[t.actor.username] += 1
        from_stranger[t.actor.username] += 1
    else:
        # add to strangers if target user not yet seen
        if t.target.username not in stranger_usernames:
            stranger_usernames[t.target.username] = t.target
        s_trans[t.target.username] += 1
        to_stranger[t.target.username] += 1

# rank friends by most to least prolific (either public or not)
sorted_ftrans = sorted(f_trans.items(), key=lambda kv: kv[1], reverse=True)
# top 5 friends based on visible transactions
print('Top Friends (by number of transactions)')
for i in range(min(len(sorted_ftrans), 5)):
    fr = sorted_ftrans[i][0]
    print(str(i + 1) + '.', '' if args.anon else fr, 
            '(', friend_usernames[fr].first_name, 
            friend_usernames[fr].last_name ,') :', sorted_ftrans[i][1])

print()
# anonymize strangers if needed
if args.anon:
    utils.anonymize(stranger_usernames)
# rank non-friends by most to least prolific
sorted_strans = sorted(s_trans.items(), key=lambda kv: kv[1], reverse=True)
print('Top Non-Friends (by number of transactions)')
for i in range(min(len(sorted_strans), 5)):
    nfr = sorted_strans[i][0]
    print(str(i + 1) + '.', '' if args.anon else nfr, 
            '(', stranger_usernames[nfr].first_name, 
            stranger_usernames[nfr].last_name ,') :', sorted_strans[i][1])
    
all_usernames = {**stranger_usernames, **friend_usernames}
print()
# rank people you pay the most
sorted_totrans = sorted({**to_friend, **to_stranger}.items(), key=lambda kv: kv[1], reverse=True)
print('Top People You Pay (by number of transactions)')
for i in range(min(len(sorted_totrans), 5)):
    nfr = sorted_totrans[i][0]
    print(str(i + 1) + '.', '' if args.anon else nfr,
           '(', all_usernames[nfr].first_name, 
            all_usernames[nfr].last_name ,') :', sorted_totrans[i][1])

print()
# rank people who pay you the most
sorted_fromtrans = sorted({**from_friend, **from_stranger}.items(), key=lambda kv: kv[1], reverse=True)
print('Top People Who Pay You (by number of transactions)')
for i in range(min(len(sorted_fromtrans), 5)):
    nfr = sorted_fromtrans[i][0]
    print(str(i + 1) + '.', '' if args.anon else nfr,
           '(', all_usernames[nfr].first_name, 
            all_usernames[nfr].last_name ,') :', sorted_fromtrans[i][1])


# recommend possible friends to test user
# we weight by number of transactions between you and friend
recs = defaultdict(int)
for fr_name, count in sorted_ftrans[:utils.MAX_REC_FRIENDS]:
    fr = friend_usernames[fr_name]
    # get friend's transactions for potential mutual users
    pages = utils.MAX_REC_TRANSACTIONS // 50 + 1
    fr_transactions = utils.get_all_user_transactions(client, fr.id, pages)
    for fr_t in fr_transactions[:utils.MAX_REC_TRANSACTIONS]:
        # don't count yourself
        if test_user.username in [fr_t.actor.username, fr_t.target.username]:
            continue
        # add to score
        if fr_t.actor.username not in friend_usernames:
            recs[fr_t.actor.username] += 1 + count / len(transactions)
        # add to strangers if not already there
        if fr_t.actor.username not in stranger_usernames:
            stranger_usernames[fr_t.actor.username] = fr_t.actor
        # add to score
        if fr_t.target.username not in friend_usernames:
            recs[fr_t.target.username] += 1 + count / len(transactions)
        # add to strangers if not already there
        if fr_t.target.username not in stranger_usernames:
            stranger_usernames[fr_t.target.username] = fr_t.target

# anonymize strangers if needed
if args.anon:
    utils.anonymize(stranger_usernames)

print()
sorted_recs = sorted(recs.items(), key=lambda kv: kv[1], reverse=True)
print('Top Friend Recommendations') 
for i in range(min(len(sorted_recs), 5)):
    rec = sorted_recs[i][0]
    print(str(i + 1) + '.', '' if args.anon else rec , 
            '(', stranger_usernames[rec].first_name, 
            stranger_usernames[rec].last_name ,')') 

# Senmo for text recognition?
print()
