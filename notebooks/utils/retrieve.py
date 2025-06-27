import requests
from pprint import pprint
from datetime import datetime, timezone
import pandas as pd

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0'}

def get_time():
    now = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    return now

def get_mastercard_rate(sgd_amount):
    url = 'https://www.mastercard.com/settlement/currencyrate/conversion-rate'
    params = {'fxDate':'0000-00-00', # current rate
            'transCurr': 'SGD', 
            'crdhldBillCurr': 'MYR', 
            'bankFee': 0, 
            'transAmt': sgd_amount}
    
    response = requests.get(url=url, headers=headers, params=params)

    result = response.json()['data']

    ratio = result['conversionRate']
    # alternatively:
    # ratio = result['crdhldBillAmt'] / result['transAmt']

    assert ratio > 3 and ratio < 3.6

    return {'MASTERCARD': ratio}

def get_wise_rate(sgd_amount):
    url = 'https://api.wise.com/v3/quotes/'
    params = {'sourceCurrency': 'MYR', 
            'targetCurrency': 'SGD', 
            'sourceAmount': 'null', 
            'targetAmount': sgd_amount }

    x = requests.post(url, json = params, headers=headers)

    results = [i for i in x.json()['paymentOptions'] if i['payIn'] in ['BALANCE', 'BANK_TRANSFER']]

    # results = {'WISE_FROM_'+r['payIn']: {r['sourceCurrency']: r['sourceAmount'], r['targetCurrency']:r['targetAmount']} for r in results}
    results = {'WISE_FROM_'+r['payIn']: r['sourceAmount'] / r['targetAmount'] for r in results}
    for r in results.values():
        assert r > 3 and r < 3.6
    
    return results

def get_results(sgd_amount):
    time = get_time()

    def get_single_amount(amt):
        rates = dict()
        rates.update(get_mastercard_rate(amt))
        rates.update(get_wise_rate(amt))
        rates = tuple(rates.items())
        rates_df = pd.DataFrame.from_records(rates, columns=['converter', 'rate'])
        rates_df['sgd_amount'] = amt
        return rates_df

    if not isinstance(sgd_amount, list):
        df = get_single_amount(sgd_amount)
        df['utc_time'] = time

    elif isinstance(sgd_amount, list):
        df = [get_single_amount(amt) for amt in sgd_amount]
        df = pd.concat(df, ignore_index=True)

    df['utc_time'] = time
    return df