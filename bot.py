#!/usr/bin/env python
__author__ = 'chase.ufkes'

import time
import json
import gc
from modules import bittrex
from modules import orderUtil
from modules import buyUtil
from modules import sellUtil
import logging

logging.basicConfig(level=logging.INFO, filename="bittrex.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

with open("config/botConfig.json", "r") as fin:
    config = json.load(fin)

apiKey = str(config['apiKey'])
apiSecret = str(config['apiSecret'])
trade = config['trade']
currency = config['currency']
sellValuePercent = config.get('sellValuePercent', 4)
buyValuePercent = config.get('buyValuePercent', 4)
volumePercent = config.get('volumePercent', 4)
buyDifference = config.get('buyDifference', 0)
extCoinBalance = config.get('extCoinBalance', 0)
checkInterval = config.get('checkInterval', 30)
initialSellPrice = config.get('initialSellPrice', 0)
tradeAmount = config.get('tradeAmount', 0)
blockSell = config.get('blockSell', 'false')
blockBuy = config.get('blockBuy', 'false')

if (initialSellPrice != 0):
    initialSellPrice = config['initialSellPrice']
    float(initialSellPrice)
    logging.info(initialSellPrice)

api = bittrex.bittrex(apiKey, apiSecret)
market = '{0}-{1}'.format(trade, currency)

def control_sell_orders(orderInventory):
    orders = sellUtil.sellNumber(orderInventory)
    if (orders == 1):
        return 1
    elif (orders > 1):
        sellUtil.cancelOrder(orderInventory, orders, apiKey, apiSecret)
    else:
        return 0

def control_buy_orders(orderInventory):
    orders = buyUtil.buyNumber(orderInventory)
    if (orders == 1):
        return 1
    elif (orders > 1):
        buyUtil.cancelOrder(orderInventory, orders, apiKey, apiSecret)
    else:
        return 0

def set_initial_buy(buyVolume, market, buyValuePercent, currentValue, tradeAmount):
    newBuyValue = buyUtil.defBuyValue(currentValue, buyValuePercent)
    if (tradeAmount == 0):
        tradeAmount = buyVolume
    logging.info("Currency: " + market)
    logging.info("Buy Value: " + str(newBuyValue))
    logging.info("Buy Volume: " + str(tradeAmount))
    logging.info("Setting buy order...")
    result = api.buylimit(market, tradeAmount, newBuyValue)
    logging.info(result)

def set_initial_sell(sellVolume, market, sellValuePercent, currentValue, tradeAmount):
    if (initialSellPrice > currentValue):
        logging.info("Setting user defined sell value")
        newSellValue = initialSellPrice
    else:
        logging.info("Setting sellValue to market conditions")
        newSellValue = sellUtil.defSellValue(currentValue, sellValuePercent)
    if (tradeAmount == 0):
        tradeAmount = sellVolume
    logging.info("Currency: " + market)
    logging.info("Sell Value: " + str(newSellValue))
    logging.info("Sell volume: " + str(tradeAmount))
    logging.info("Setting sell order...")
    result = api.selllimit(market, tradeAmount, newSellValue)
    logging.info(result)


volumePercent = volumePercent * .01
buyDifference = buyDifference * .01
balance = api.getbalance(currency)['Balance'] + extCoinBalance
buyVolume = buyUtil.newBuyVolume(balance, volumePercent, buyDifference)
sellVolume = balance * volumePercent


logging.info("checking value")
currentValue = orderUtil.initialMarketValue(market, apiKey, apiSecret)
orderInventory = orderUtil.orders(market, apiKey, apiSecret) #prepare to reset orders
orderUtil.resetOrders(orderInventory, apiKey, apiSecret)
balance = api.getbalance(currency)['Balance'] + extCoinBalance
buyVolume = buyUtil.newBuyVolume(balance, volumePercent, buyDifference)
sellVolume = balance * volumePercent

if blockBuy == 'false':
    logging.info(tradeAmount)
    set_initial_buy(buyVolume, market, buyValuePercent, currentValue, tradeAmount)
if blockSell == 'false':
    logging.info(tradeAmount)
    set_initial_sell(sellVolume, market, sellValuePercent, currentValue, tradeAmount)
time.sleep(2)

cycle = 0

while True:
    cycle = cycle + 1
    try:
        orderInventory = orderUtil.orders(market, apiKey, apiSecret)
        orderUtil.recentTransaction(market, orderInventory, apiKey, apiSecret, checkInterval)
        orderValueHistory = orderUtil.lastOrderValue(market, apiKey, apiSecret)
        balance = api.getbalance(currency)['Balance'] + extCoinBalance

        if blockSell == 'false':
            sellControl = control_sell_orders(orderInventory)
            if (sellControl == 0):
                newSellValue = sellUtil.defSellValue(orderValueHistory, sellValuePercent)
                if (tradeAmount == 0):
                    newSellVolume = balance * volumePercent
                logging.info("Currency: " + currency)
                logging.info("Sell Value: " + str(newSellValue))
                logging.info("Sell volume: " + str(newSellVolume))
                logging.info("Setting sell order...")
                result = api.selllimit(market, newSellVolume, newSellValue)
                logging.info(result)



        if blockBuy == 'false':
            buyControl = control_buy_orders(orderInventory)
            if (buyControl == 0):
                newBuyValue = buyUtil.defBuyValue(orderValueHistory, buyValuePercent)
                if (tradeAmount == 0):
                    newBuyVolume = buyUtil.newBuyVolume(balance, volumePercent, buyDifference)
                logging.info("Currency: " + currency)
                logging.info("Buy Value: " + str(newBuyValue))
                logging.info("Buy Volume: " + str(newBuyVolume))
                logging.info("Setting buy order...")
                result = api.buylimit(market, newBuyVolume, newBuyValue)
                logging.info(result)

    except:
        logging.info("Bittrex probably threw a 503...trying again on the next cycle")

    if cycle == 100:
        logging.info("Garbage collection")
        gc.collect()
        count = 0
    time.sleep(checkInterval)