# evaluate training results trained by PVQTrain.py, realize, that it is not based exactly same calculation as reward is calculated at training 
# example copypaste down, see the models directory for existence of model .h5 
# python PVQEvaluate.py RLDataForCL30 RLDataForCL30_500 
# Programming marko.rantala@pvoodoo.com
# v1.0.0.1 20190305 
##############################
# my own ad: For NinjaTrader related stuff: check https://pvoodoo.com or blog: https://pvoodoo.blogspot.com/?view=flipcard
##############################


import keras
import matplotlib.pyplot as plt
from keras.models import load_model

from agent.PVAgent import PVAgent
from functions import *
import sys
import constant

if len(sys.argv) != 3:
	print("Usage: python evaluate.py [stock] [model] ")
	exit()

stock_name, model_name = sys.argv[1], sys.argv[2] 
model = load_model("models/" + model_name +".h5")  # sort of duplicate just to get feature count!!, bad programming... 
#feature_count = model.layers[0].input.shape.as_list()[1]
if Debug:
    print(model.layers[0].input.shape.as_list())
timesteps = model.layers[0].input.shape.as_list()[1]

prices, data = getStockDataVec(stock_name, timesteps, model_name=model_name)
agent = PVAgent(data.shape[1], data.shape[2], is_eval=True, model_name=model_name)

l = len(data) - 1
batch_size = 32


total_profit = 0.0
agent.inventory = []

market_state = getState(data, 0)
position_state = np.array([1,0,0,0.0]).reshape(1,4) # [Flat,Long,Short,PnL]  what the hell is turning this ... 
state = [market_state, position_state]

ts_buy = []
ts_sell = []
ts_PnL =  np.zeros(l)
ts_CumPnL = np.zeros(l)
ts_Action = np.zeros(l)

for t in range(l):
    action = agent.act(state)
    ts_Action[t] = action

    next_market_state = getState(data, t + 1)
    
  
    if (action == 1) and (state[1][0][1] < constant.MAXCONTRACTS):# buy
        ts_buy.append(t)
        if Debug:
            print("Buy before, state",state[1][0])
    elif action == 2 and state[1][0][2] < constant.MAXCONTRACTS: # sell
        ts_sell.append(t)
        if Debug:
            print("Sell before, state",  state[1][0])
        
    next_position_state, immediate_reward, PnL = getNextPositionState(action, state[1][0], prices[t], prices[t+1])
    total_profit += PnL*constant.POINTVALUE
 
    if (Debug):
        if (action == 1) and (state[1][0][1] < constant.MAXCONTRACTS):# buy
            print("Buy after", next_position_state, PnL)
        elif action == 2 and state[1][0][2] < constant.MAXCONTRACTS: # sell 
            print("Sell after",  next_position_state, PnL)

    if PnL != 0.0:
        ts_PnL[t] = PnL*constant.POINTVALUE
    ts_CumPnL[t] = total_profit 
    
    done = True if t == l - 1 else False
    next_state = [next_market_state, next_position_state.reshape(1,4)]
 
    #agent.memory.append((state, action, reward, next_state, done))
    state = next_state
    
    
    if done:
        print("--------------------------------")
        print(stock_name + " Total Profit (USD): ", total_profit)
        print("--------------------------------")

        
        
# hi, matplot gurus, please help here :)        

data = np.array(prices)
ts = np.arange(l).astype(int)
ts_buy = np.array(ts_buy).astype(int)
ts_sell = np.array(ts_sell).astype(int)

fig, ax1 = plt.subplots()

ax2 = ax1.twinx()

ax2.plot(ts, data[ts], zorder=3)
ax2.scatter(ts_buy, data[ts_buy], c="g", label="Buy")
ax2.scatter(ts_sell, data[ts_sell], c="r", label="Sell")
ax2.set_ylabel('Price')

ax1.set_ylabel('PnL, USD')
ax1.bar(ts, ts_PnL, color="b", label="PnL", width=3.0, zorder=2)
ax1.plot(ts, ts_CumPnL, color="c", label="Cumulative PnL", zorder=1)
ax1.bar(ts, ts_Action, color="r", label="Action", width=1.0, zorder=4)
ax1.axhline(0, color='gray', lw=1)


plt.legend()
fig.tight_layout() 
plt.show()