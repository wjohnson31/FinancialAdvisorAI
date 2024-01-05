from openai import OpenAI
import pandas as pd
import json
import streamlit as st
import matplotlib.pyplot as plt
import yfinance as yf

client = OpenAI(api_key=open('API_KEY', 'r').read())

def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1].Close)

def calculate_SMA(ticker,window):
    data = yf.Ticker(ticker).history(period='1y').iloc[-1].Close
    return str(data.rolling(window=window).mean().iloc[-1])

def calculate_EMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').iloc[-1].Close
    return str(data.ewm(span=window, adjust = False).mean().iloc[-1])
def calculate_RSI(ticker):
    data = yf.Ticker(ticker).history(period='1y').iloc[-1].Close
    change = data.diff()
    up = change.clip(lower=0)
    down = -1 * up
    ema_up = up.ewm(com=14-1, adjust = False).mean()
    ema_down =down.ewm(com=14-1, adjust = False).mean()
    rs = ema_up / ema_down
    return str(100 - (100/ (1 + rs)).iloc[-1])
def calculate_MACD(ticker):
    data = yf.Ticker(ticker).history(period='1y').iloc[-1].Close
    short_EMA = data.ewm(span = 12, adjust = False).mean()
    long_EMA = data.ewm(span = 26, adjust = False).mean()

    MACD = short_EMA - long_EMA
    signal = MACD.ewm(span = 9, adjust = False).mean()
    MACD_histogram = MACD - signal
    return f'{MACD[-1]}, {signal[-1]}, {MACD_histogram[-1]}'
def plot_stock_prices(ticker):
    data = yf.Ticker(ticker).history(period='1y')
    dates = data.index
    prices = data['Close']
    plt.figure(figsize=(10, 6))
    plt.plot(dates, prices, label=f'{ticker} Stock Prices', color='blue')
    plt.title(f'Stock Prices for {ticker} over the last year')
    plt.xlabel('Date')
    plt.ylabel('Closing Price (USD)')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.close

functions = [
    {
        'name': 'get_stock_price',
        'description': 'gets the latest stock price given the ticker symbol of a company.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker':   {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company(For example, AMZN for Amazon.com).'
                }
            },
            'required': ['ticker']
        }
    },
    {
        'name': 'calculate_SMA',
        'description': 'Calculates the simple moving average for a given stock ticker and a window',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker':   {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company(For example, AMZN for Amazon.com).'
                },
                'window': {
                    'type': 'integer',
                    'description:': 'The timeframe to use when calculating the SMA'
                }
            },
            'required': ['ticker', 'window']
        }
    },
    {
        'name': 'calculate_EMA',
        'description': 'Calculates the exponential moving average for a given stock ticker and a window',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker':   {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company(For example, AMZN for Amazon.com).'
                },
                'window': {
                    'type': 'integer',
                    'description:': 'The timeframe to use when calculating the SMA'
                }
            },
            'required': ['ticker','window']
        }
    },
    {
        'name': 'calculate_RSI',
        'description': 'Calculates the relative strength index of a given stock ticker',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker':   {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company(For example, AMZN for Amazon.com).'
                }
            },
            'required': ['ticker']
        }
    },
    {
        'name': 'calculate_MACD',
        'description': 'Calculates the moving average convergence divergence of a given stock ticker',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker':   {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company(For example, AMZN for Amazon.com).'
                }
            },
            'required': ['ticker']
        }
    },
    {
        'name': 'plot_stock_prices',
        'description': 'plots the stock prices of a given stock ticker over the past year.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker':   {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company(For example, AMZN for Amazon.com).'
                }
            },
            'required': ['ticker']
        }
    }
]   
avaliable_functions = {
    'get_stock_price': get_stock_price,
    'calculate_SMA': calculate_SMA,
    'calculate_EMA': calculate_EMA,
    'calculate_RSI': calculate_RSI,
    'calculate_MACD': calculate_MACD,
    'plot_stock_prices': plot_stock_prices
}

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

st.title('Personal AI Stock Assistant')
user_input = st.text_input("Ask your financial assistant anything")
if user_input:
    try:
        st.session_state['messages'].append({"role": "user", "content":f'{user_input}'})

        response = client.chat.completions.create(
            model = 'gpt-3.5-turbo-0613',
            messages = st.session_state['messages'],
            functions = functions,
            function_call = 'auto',
        )
        response_message = response['choices'][0]['message']['content']

        if response_message.get('function_call'):
            function_name = response_message['function call']['name']
            function_args = json.loads(response_message['function_call']['arguments'])
            if function_name in ['get_stock_price', 'calculate_RSI', 'plot_stock_prices', 'calculate_MACD']:
                args_dict = {'ticker': function_args.get('ticker')}
            elif function_name in ['calculate_SMA', 'calculate_EMA']:
                args_dict = {'ticker': function_args.get('ticker'), 'window': function_args.get('window')}

            function_to_call = avaliable_functions[function_name]
            function_response = function_to_call(**args_dict)

            if function_name == 'plot_stock_prices':
                st.image('stock.png')
            else:
                st.session_state['messages'].append(response_message)
                st.session_state['messages'].append(
                    {
                        'role': 'function',
                        'name': function_name,
                        'content': function_response
                    }
                )
                second_response = client.chat.completions.create(
                    model = 'gpt-3.5-turbo-0613',
                    messages = st.session_state['messages']
                )
                st.text(second_response['choices'][0]['message']['content'])
                st.session_state['messages'].append({'role': 'assistant', 'content': second_response['choices'][0]['message']['content']})
        else:
            st.text(response_message['content'])
            st.session_state['messages'].append({'role': 'assistant', 'content': response_message['content']})
    except Exception as e:
        raise e
        ##st.text('Error occured, ', str(0))
                
