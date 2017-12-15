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
sellVolumePercent = config.get('sellVolumePercent', 0)
buyValuePercent = config.get('buyValuePercent', 4)
buyVolumePercent = config.get('buyVolumePercent', 0)
extCoinBalance = config.get('extCoinBalance', 0)
checkInterval = config.get('checkInterval', 30)
initialSellPrice = config.get('initialSellPrice', 0)
tradeAmount = config.get('tradeAmount', 0)

if (initialSellPrice != 0):
    initialSellPrice = config['initialSellPrice']
    float(initialSellPrice)
    logging.info(initialSellPrice)

if (sellValuePercent == 0):
    blockSell = 'true'
else:
    blockSell = 'false'

if (buyValuePercent == 0):
    blockBuy = 'true'
else:
    blockBuy = 'false'

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

def set_initial_buy(buyVolumePercent, orderVolume, market, buyValuePercent, currentValue):
    newBuyValue = buyUtil.defBuyValue(currentValue, buyValuePercent)
    if (buyVolumePercent == 0):
        newBuyVolume = tradeAmount
    else:
        newBuyVolume = buyUtil.defBuyVolume(orderVolume, buyVolumePercent)
    result = api.buylimit(market, newBuyVolume, newBuyValue)
    logging.info(result)

def set_initial_sell(sellVolumePercent, orderVolume, market, sellValuePercent, currentValue):
    if (initialSellPrice > currentValue):
        logging.info("Setting user defined sell value")
        newSellValue = initialSellPrice
    else:
        logging.info("Setting sellValue to market conditions")
        newSellValue = sellUtil.defSellValue(currentValue, sellValuePercent)
    if (sellVolumePercent == 0):
        newSellVolume = tradeAmount
    else:
        newSellVolume = sellUtil.defSellVolume(orderVolume, sellVolumePercent)
    result = api.selllimit(market, newSellVolume, newSellValue)
    logging.info(result)

for i in range(0,10):
    while True:
        try:
            logging.info("checking value")
            currentValue = orderUtil.initialMarketValue(market, apiKey, apiSecret)
            orderInventory = orderUtil.orders(market, apiKey, apiSecret) #prepare to reset orders
            orderUtil.resetOrders(orderInventory, apiKey, apiSecret)
            orderVolume = api.getbalance(currency)['Balance'] + extCoinBalance

            if blockBuy == 'false':
                logging.info(tradeAmount)
                set_initial_buy(buyVolumePercent, orderVolume, market, buyValuePercent, currentValue)
            if blockSell == 'false':
                logging.info(tradeAmount)
                set_initial_sell(sellVolumePercent, orderVolume, market, sellValuePercent, currentValue)
            time.sleep(2)
        except:
            logging.info("Bittrex threw an error...")
            continue
        break
    break


cycle = 0

while True:
    cycle = cycle + 1
    try:
        orderInventory = orderUtil.orders(market, apiKey, apiSecret)
        orderUtil.recentTransaction(market, orderInventory, apiKey, apiSecret, checkInterval)
        orderValueHistory = orderUtil.lastOrderValue(market, apiKey, apiSecret)
        orderVolume = api.getbalance(currency)['Balance'] + extCoinBalance

        if blockSell == 'false':
            sellControl = control_sell_orders(orderInventory)
            if (sellControl == 0):
                newSellValue = sellUtil.defSellValue(orderValueHistory, sellValuePercent)
                if (sellVolumePercent == 0):
                    logging.info("Setting user defined trade amount ")
                    logging.info(tradeAmount)
                    newSellVolume = tradeAmount
                else:
                    newSellVolume = sellUtil.defSellVolume(orderVolume, sellVolumePercent)
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
                if (buyVolumePercent == 0):
                    logging.info("Setting user defined trade amount ")
                    logging.info(tradeAmount)
                    newBuyVolume = tradeAmount
                else:
                    newBuyVolume = buyUtil.defBuyVolume(orderVolume, buyVolumePercent)
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
