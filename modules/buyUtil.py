__author__ = 'chase.ufkes'

import bittrex

def buyNumber(orderInventory):
    orderCount = 0
    for order in orderInventory:
        if (order['OrderType'] == 'LIMIT_BUY'):
            orderCount = orderCount + 1
    return orderCount

def defBuyValue(orderHistory, buyValuePercent):
    newBuyValue = round(orderHistory - (orderHistory * (buyValuePercent * .01)), 8)
    return newBuyValue

def defBuyVolume(orderVolume, buyVolumePercent):
    newBuyVolume = round((orderVolume * (buyVolumePercent * .01)), 8)
    return newBuyVolume

def cancelOrder(orderInventory, orders, apiKey, apiSecret):
    api = bittrex.bittrex(apiKey, apiSecret)
    ordersToKill = orders - 1
    for buyOrder in orderInventory:
        while (ordersToKill >  0):
            api.cancel(buyOrder['OrderUuid'])
            ordersToKill = ordersToKill - 1

def newBuyVolume(balance, volumePercent, buyDifference):
    return balance * volumePercent * (1/(1 - volumePercent) * 1 + buyDifference)

