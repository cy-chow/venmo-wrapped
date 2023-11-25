import venmo_api as venmo
import emoji
from datetime import datetime

# constants

DEFAULT_TOKEN_FILE = 'access_token.txt'
DEFAULT_TOTAL_PAGES = 4

MAX_REC_TRANSACTIONS = 20
MAX_REC_FRIENDS = 5


# Note: assumes no user has more than 1000 transactions
def get_all_user_transactions(client: venmo.Client, user_id, max_pages = 20):
    transaction_pages = paginate_transactions(client, user_id, max_pages)
    # flatten transactions
    return [t for page in transaction_pages for t in page]

# return transactions as a page
def paginate_transactions(client: venmo.Client, user_id, max_pages=10):
    transactions = client.user.get_user_transactions(user_id=user_id)
    transaction_pages = []
    i = 0
    # continue only if there are still more pages and we have not
    # yet reached the max pages limit
    while transactions and i < max_pages:
        transaction_pages.append(transactions)
        transactions = transactions.get_next_page()
        i += 1
    return transaction_pages

'''
# save flattened list from get_all_user_transactions to csv/dataframe
def save_transactions(user_id, transactions: list):
    transactions_dict = {}
    for t in transactions:
        # skip duplicate transactions
        if t.id in transactions_dict:
            continue

        # add transaction to data dict
        payer = t.target if t.payment_type == 'charge' else  t.actor
        payee = t.actor if t.payment_type == 'charge' else  t.target
        transactions_dict[t.id] = [
            t.id,
            payer.display_name,
            payee.display_name,
            emoji.demojize(t.note),
            datetime.fromtimestamp(t.date_created),
        ]

    transactions_df = pd.DataFrame.from_dict(transactions_dict, orient='index', columns=[
        'TransactionId',
        'Source',
        'Target',
        'Label',
        'Timestamp',
    ])

    transactions_df.to_csv(f'data/transactions_{user_id}.csv', index=False)
    '''

def anonymize(users_dict):
    # only use first and last initials
    for name, user in users_dict.items():
        users_dict[name].first_name = user.first_name[:1]
        users_dict[name].last_name = user.last_name[:1]
