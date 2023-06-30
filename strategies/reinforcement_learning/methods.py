import logging
import numpy as np
from tqdm import tqdm
from .ops import get_state, format_quantity, format_notional


def train_model(agent, episode, data, ep_count=100, batch_size=32, window_size=10):
    total_profit = 0
    data_length = len(data) - 1

    agent.inventory = []
    avg_loss = []

    state = get_state(data, 0, window_size + 1)

    for t in tqdm(range(data_length), total=data_length, leave=True, desc='Episode {}/{}'.format(episode, ep_count)):
        reward = 0
        next_state = get_state(data, t + 1, window_size + 1)

        # select an action
        action = agent.act(state)

        # BUY
        if action == 1:
            agent.inventory.append(data[t])

        # SELL
        elif action == 2 and len(agent.inventory) > 0:
            bought_price = agent.inventory.pop(0)
            profit = data[t] - bought_price
            reward = profit  # max(profit, 0)
            total_profit += profit

        # HOLD
        else:
            pass

        done = (t == data_length - 1)
        agent.remember(state, action, reward, next_state, done)

        if len(agent.memory) > batch_size:
            loss = agent.train_experience_replay(batch_size)
            avg_loss.append(loss)

        state = next_state

    #if episode % 10 == 0:
    agent.save(episode)

    return (episode, ep_count, total_profit, np.mean(np.array(avg_loss)))


def evaluate_model(agent, data, window_size, debug):
    total_cash = 0
    total_profit = 0
    data_length = len(data) - 1

    history = []
    agent.inventory = []

    state = get_state(data, 0, window_size + 1)

    for t in range(data_length):
        # reward = 0
        next_state = get_state(data, t + 1, window_size + 1)

        # select an action
        action = agent.act(state, is_eval=True)

        # BUY
        if action == 1:
            agent.inventory.append(data[t])

            history.append((data[t], "BUY"))
            if debug:
                total_shares = len(agent.inventory)
                total_mv = data[t] * total_shares
                total_cash -= data[t]
                logging.debug("Day {} Buy at: {} | Shares: {} | MV: {} | Cash: {}".format(
                    t,
                    format_notional(data[t]),
                    format_quantity(total_shares),
                    format_notional(total_mv),
                    format_notional(total_cash)
                ))

        # SELL
        elif action == 2 and len(agent.inventory) > 0:
            bought_price = agent.inventory.pop(0)
            profit = data[t] - bought_price
            # reward = profit  # max(profit, 0)
            total_profit += profit

            history.append((data[t], "SELL"))
            if debug:
                total_shares = len(agent.inventory)
                total_mv = data[t] * total_shares
                total_cash += data[t]
                logging.debug("Day {} Sell at: {} | Shares: {} | MV: {} | Cash: {} | Profit: {} | Total Profit: {}".format(
                    t,
                    format_notional(data[t]),
                    format_quantity(total_shares),
                    format_notional(total_mv),
                    format_notional(total_cash),
                    format_notional(profit),
                    format_notional(total_profit)
                ))

        # HOLD
        else:
            history.append((data[t], "HOLD"))

        done = (t == data_length - 1)
        # FIXME: Test data should not be memorized???
        # agent.memory.append((state, action, reward, next_state, done))

        state = next_state
        if done:
            return total_profit, history
