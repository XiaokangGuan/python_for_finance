import logging
import numpy as np
from tqdm import tqdm
from .ops import get_state, format_quantity, format_notional, log_daily_flash


def train_model(agent, episode, data, ep_count=100, batch_size=32, window_size=10):
    # Initial portfolio
    initial_mv = 0
    initial_cash = 0
    initial_portfolio = initial_mv + initial_cash

    data_length = len(data) - 1

    # Reset starting point
    mv = initial_mv
    cash = initial_cash
    portfolio = initial_portfolio
    agent.inventory = []
    avg_loss = []
    state = get_state(data, 0, window_size + 1)

    for t in tqdm(range(data_length), total=data_length, leave=True, desc='Episode {}/{}'.format(episode, ep_count)):
        # Reward is defined as entire portfolio value change from state to next_state,
        # i.e. including both stock MV change (due to action / price change) and cash change.

        # Select an action
        action = agent.act(state)

        # BUY
        if action == 1:
            agent.inventory.append(data[t])
            next_mv = data[t+1] * len(agent.inventory)
            next_cash = cash - data[t]
            next_portfolio = next_mv + next_cash

        # SELL
        elif action == 2 and len(agent.inventory) > 0:
            agent.inventory.pop(0)
            next_mv = data[t + 1] * len(agent.inventory)
            next_cash = cash + data[t]
            next_portfolio = next_mv + next_cash

        # HOLD
        else:
            next_mv = data[t + 1] * len(agent.inventory)
            next_cash = cash
            next_portfolio = next_mv + next_cash

        # Memorize
        reward = next_portfolio - portfolio
        done = (t == data_length - 1)
        next_state = get_state(data, t + 1, window_size + 1)
        agent.remember(state, action, reward, next_state, done)

        # Train on experience
        if len(agent.memory) > batch_size:
            loss = agent.train_experience_replay(batch_size)
            avg_loss.append(loss)

        state = next_state
        mv = next_mv
        cash = next_cash
        portfolio = next_portfolio

    agent.save(episode)

    total_profit = portfolio - initial_portfolio
    return episode, ep_count, total_profit, np.mean(np.array(avg_loss))


def evaluate_model(agent, data, window_size, debug):
    # Initial portfolio
    initial_shares = 0
    initial_mv = 0
    initial_cash = 0
    initial_portfolio = initial_mv + initial_cash

    data_length = len(data) - 1

    # Reset starting point
    shares = initial_shares
    mv = initial_mv
    cash = initial_cash
    agent.inventory = []
    state = get_state(data, 0, window_size + 1)
    history = []

    for t in range(data_length):
        # Select an action
        action = agent.act(state, is_eval=True)

        # BUY
        if action == 1:
            action_name = 'BUY'
            agent.inventory.append(data[t])

            next_shares = len(agent.inventory)
            next_mv = data[t + 1] * next_shares
            next_cash = cash - data[t]

        # SELL
        elif action == 2 and len(agent.inventory) > 0:
            action_name = 'SELL'
            agent.inventory.pop(0)

            next_shares = len(agent.inventory)
            next_mv = data[t + 1] * next_shares
            next_cash = cash + data[t]

        # HOLD
        else:
            action_name = 'HOLD'

            next_shares = len(agent.inventory)
            next_mv = data[t + 1] * next_shares
            next_cash = cash

        history.append((data[t], action_name))
        if debug:
            log_daily_flash(t, action_name, data[t], shares, mv, cash, next_shares, next_mv, next_cash, initial_portfolio)

        done = (t == data_length - 1)
        next_state = get_state(data, t + 1, window_size + 1)

        state = next_state
        shares = next_shares
        mv = next_mv
        cash = next_cash

        total_profit = mv + cash - initial_portfolio
        if done:
            return total_profit, history
