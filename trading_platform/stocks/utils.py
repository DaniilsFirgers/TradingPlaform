import requests
import os
import time
from numerize import numerize
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import base64
from io import BytesIO


def make_data_request(ticker):
    token = os.environ["SECRET_API_TOKEN"]
    response = requests.get("https://cloud.iexapis.com/stable/stock/{}/quote?token={}".format(ticker, token))
    return response


def make_chart_data_request(ticker, range, date):
    token = os.environ["SECRET_API_TOKEN"]
    response = requests.get("https://cloud.iexapis.com/stable/stock/{}/chart/{}/{}?token={}".format(ticker, range, date, token))
    return response


def make_news_data_request(ticker, articles):
    token = os.environ["SECRET_API_TOKEN"]
    response = requests.get(
        "https://cloud.iexapis.com/stable/stock/{}/news/last/{}?token={}".format(ticker, articles, token))
    return response


def get_client_stock_details(positions, max_retries=10, retry_after=1):

    """Gets various metrics from IEX API for a client's positions"""

    output_data = []

    for position in positions:
        ticker = position.symbol
        response = make_data_request(ticker)
        status_code = response.status_code

        while status_code == 429 and max_retries:
            time.sleep(retry_after)
            response = make_data_request(ticker)
            status_code = response.status_code
            max_retries -= 1
            retry_after += 1

        # raise an exception if API response is not 200
        if status_code != 200:
            raise Exception(f"IEX api failed with the following status code: {status_code}. "
                            f"Most likely one of the tickers is invalid")

        stock_data = response.json()

        price = stock_data['latestPrice']
        change = stock_data['change']
        percentage_change = 100 * (stock_data['changePercent'] or 0.00)

        # making a data dictionary with a desired set of financial metrics
        data_dict = {
            "Name": position.name,
            "Ticker": ticker,
            "Shares": position.shares,
            "Last_Price": price,
            "Day_Change": change,
            "Day_Change_prc": percentage_change,
        }
        output_data.append(data_dict)

    return output_data


def get_stock_price(ticker, max_retries=10, retry_after=1):

    """Gets the latest price for a specific stock"""

    price = ""
    response = make_data_request(ticker)
    status_code = response.status_code

    while status_code == 429 and max_retries:
        time.sleep(retry_after)
        response = make_data_request(ticker)
        status_code = response.status_code
        max_retries -= 1
        retry_after += 1

    # if the response status is 404 then there is no info about the price for the ticker
    if status_code == 404 :
        price = "-"
    # if the response status is not 404 then retrieve the latest price
    else:
        stock_data = response.json()
        price = stock_data['latestPrice']

    return price


def get_individual_stock_details(ticker, max_retries=10, retry_after=1):

    """Gets financial metrics for a stock"""

    response = make_data_request(ticker)
    status_code = response.status_code

    while status_code == 429 and max_retries:
        time.sleep(retry_after)
        response = make_data_request(ticker)
        status_code = response.status_code
        max_retries -= 1
        retry_after += 1


    stock_data = response.json()

    # making a dictionary with a desired set of financial metrics
    data_dict = {
        "Name": stock_data['companyName'],
        "Ticker": ticker,
        "AverageTotalVolume": format(stock_data['avgTotalVolume'], ',d'),
        "Last_Price": stock_data['latestPrice'],
        "Day_Change": stock_data['change'],
        "Day_Change_prc": round(stock_data['changePercent']*100, 2),
        "MarketCap": numerize.numerize(stock_data['marketCap'], 3),
        "PeRatio": stock_data['peRatio'],
        "PreviousDayClose": stock_data['previousClose'],
        "Week52High": stock_data['week52High'],
        "Week52Low": stock_data['week52Low'],
    }

    return data_dict

def get_graph():
    """Makes an image from a matplotlib graph"""
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()

    graph = base64.b64encode(image_png)

    graph = graph.decode('utf-8')

    buffer.close()
    return graph


def make_graph(ticker, date, range, max_retries=10, retry_after=1):
    """Makes a graph for a stock's latest day prices"""

    initial_response = make_chart_data_request(ticker, range, date)
    initial_stock_data = initial_response.json()
    date_modified = datetime.strptime(date, "%Y%m%d")

    # checks whether today is saturday/sunday and if so sets the weekday to friday to extract the latest prices
    if date_modified.weekday() == 5:
        date_to_use = f"{datetime.now().year}{datetime.now().month:02}{datetime.now().day - 1:02}"
        date_modified = date_to_use
    elif date_modified.weekday() == 6:
        date_to_use = f"{datetime.now().year}{datetime.now().month:02}{datetime.now().day - 2:02}"
        date_modified = date_to_use
    elif date_modified.weekday() == 0 and not initial_stock_data:
        date_to_use = f"{datetime.now().year}{datetime.now().month:02}{datetime.now().day - 3:02}"
        date_modified = date_to_use
    elif not initial_stock_data:
        date_to_use = f"{datetime.now().year}{datetime.now().strftime('%m')}{datetime.now().day - 1:02}"
        date_modified = date_to_use
    else:
        date_modified = date

    data_dict = {
        'minute':[],
        'close_price':[],
    }

    response = make_chart_data_request(ticker, range, date_modified)
    stock_data = response.json()
    status_code = response.status_code

    while status_code == 429 and max_retries:
        time.sleep(retry_after)
        response = make_chart_data_request(ticker, range, date_modified)
        status_code = response.status_code
        max_retries -= 1
        retry_after += 1

    # populates the dictionary with the closing price and time
    for date in stock_data:
        if date['close'] == None:
            pass
        else:
            data_dict['minute'].append(date['label'])
            data_dict['close_price'].append(date['close'])

    df = pd.DataFrame.from_dict(data_dict)

    # sets color for graph - if a closing price is greater than a closing price then the color is green (upward trend)
    if df['close_price'].iloc[-1] > df['close_price'].iloc[0]:
        color = "green"
    else:
        color = "red"

    # creates a graph
    plt.switch_backend("AGG")
    plt.figure(figsize=(8, 4))
    df.plot(kind='line', x='minute', y='close_price', color=color, legend=None)
    plt.ylim(df['close_price'].min() * 0.96, df['close_price'].max() * 1.04)
    plt.xticks(rotation=45)
    plt.fill_between(x=df.index, y1=df['close_price'], color=color)
    plt.tight_layout()
    # makes a conversion into an image
    graph = get_graph()
    return graph


def get_latest_news(ticker, articles, max_retries=10, retry_after=1):

    """Gets latest articles about a certain company"""
    news_list=[]

    response = make_news_data_request(ticker, articles)
    status_code = response.status_code

    while status_code == 429 and max_retries:
        time.sleep(retry_after)
        response = make_news_data_request(ticker, articles)
        status_code = response.status_code
        max_retries -= 1
        retry_after += 1

    articles = response.json()

    for article in articles:
        article_list = {
            'headline': article['headline'],
            'url': article['url'],
            'summary': article['summary']
        }
        news_list.append(article_list)

    return news_list