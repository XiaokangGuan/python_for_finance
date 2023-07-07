import numpy as np
import pandas as pd
from tqdm import tqdm
from .ops import get_state, log_daily_flash, sigmoid
from utils.performance_evaluation import annualized_return, annualized_volatility, sharpe_ratio


def train_model(agent, episode, data, ep_count=100, batch_size=32, window_size=10, debug=False):
    agent.debug = debug

    # Initial portfolio
    initial_shares = 0
    initial_mv = 0
    initial_cash = 10000

    data_length = len(data) - 1

    # Reset starting point
    shares = initial_shares
    mv = initial_mv
    cash = initial_cash
    agent.inventory = 0
    avg_loss = []
    state = get_state(data, 0, window_size + 1, 0)

    for t in tqdm(range(data_length), total=data_length, leave=True, desc='Episode {}/{}'.format(episode, ep_count)):
        # Select an action
        action = agent.act(state)

        # BUY
        if action == 1:
            # Illegal BUY, position / cash stays same, assign penalty
            if cash < data[t]:
                action_name = 'Invalid BUY'

                next_shares = agent.inventory
                next_mv = data[t + 1] * agent.inventory
                next_cash = cash
                reward = 0
            else:
                action_name = 'BUY'
                agent.inventory += 1

                next_shares = agent.inventory
                next_mv = data[t + 1] * agent.inventory
                next_cash = cash - data[t]
                reward = sigmoid(next_mv + next_cash - mv - cash)
        # SELL
        elif action == 2:
            # Illegal SELL, position / cash stays same, assign penalty
            if agent.inventory <= 0:
                action_name = 'Invalid SELL'

                next_shares = agent.inventory
                next_mv = data[t + 1] * agent.inventory
                next_cash = cash
                reward = 0
            else:
                action_name = 'SELL'
                agent.inventory -= 1

                next_shares = agent.inventory
                next_mv = data[t + 1] * agent.inventory
                next_cash = cash + data[t]
                reward = sigmoid(next_mv + next_cash - mv - cash)
        # HOLD
        else:
            action_name = 'HOLD'

            next_shares = agent.inventory
            next_mv = data[t + 1] * agent.inventory
            next_cash = cash
            reward = sigmoid(next_mv + next_cash - mv - cash)

        if debug:
            log_daily_flash(t, action_name, data[t], shares, mv, cash, next_shares, next_mv, next_cash, initial_cash + initial_mv)

        # Memorize
        # Reward is defined as entire portfolio value change from state to next_state,
        # i.e. including both stock MV change (due to action / price change) and cash change.
        done = (t == data_length - 1)
        next_state = get_state(data, t + 1, window_size + 1, next_mv / (next_cash + next_mv))
        agent.remember(state, action, reward, next_state, done)

        # Train on experience
        if len(agent.memory) > batch_size:
            loss = agent.train_experience_replay(batch_size)
            avg_loss.append(loss)

        state = next_state
        shares = next_shares
        mv = next_mv
        cash = next_cash

    agent.save(episode)

    total_profit = mv + cash - initial_mv - initial_cash
    return episode, ep_count, total_profit, np.mean(np.array(avg_loss))


def evaluate_model(agent, start, end, data, window_size, debug):
    agent.debug = debug

    # Initial portfolio
    initial_shares = 0
    initial_mv = 0
    initial_cash = 10000

    data_length = len(data) - 1

    # Reset starting point
    shares = initial_shares
    mv = initial_mv
    cash = initial_cash
    agent.inventory = 0
    state = get_state(data, 0, window_size + 1, 0)
    history = []

    for t in range(data_length):
        # Select an action
        action = agent.act(state, is_eval=True)

        # BUY
        if action == 1:
            if cash < data[t]:
                action_name = 'Invalid BUY'

                next_shares = agent.inventory
                next_mv = data[t + 1] * agent.inventory
                next_cash = cash
            else:
                action_name = 'BUY'
                agent.inventory += 1

                next_shares = agent.inventory
                next_mv = data[t + 1] * agent.inventory
                next_cash = cash - data[t]

        # SELL
        elif action == 2:
            if agent.inventory <= 0:
                action_name = 'Invalid SELL'

                next_shares = agent.inventory
                next_mv = data[t + 1] * agent.inventory
                next_cash = cash
            else:
                action_name = 'SELL'
                agent.inventory -= 1

                next_shares = agent.inventory
                next_mv = data[t + 1] * agent.inventory
                next_cash = cash + data[t]

        # HOLD
        else:
            action_name = 'HOLD'

            next_shares = agent.inventory
            next_mv = data[t + 1] * agent.inventory
            next_cash = cash

        history.append((t, data[t], action_name, mv, cash))
        if debug:
            log_daily_flash(t, action_name, data[t], shares, mv, cash, next_shares, next_mv, next_cash, initial_cash + initial_mv)

        done = (t == data_length - 1)
        next_state = get_state(data, t + 1, window_size + 1, next_mv / (next_mv + next_cash))

        state = next_state
        shares = next_shares
        mv = next_mv
        cash = next_cash

        if done:
            # Metrics
            total_profit = mv + cash - initial_mv - initial_cash
            daily_portfolio = pd.Series([mv + cash for _, _, _, mv, cash in history])
            annual_return = annualized_return(daily_portfolio)
            annual_vol = annualized_volatility(daily_portfolio)
            sharpe = sharpe_ratio(daily_portfolio, risk_free=0.0208)
            return start, end, total_profit, annual_return, annual_vol, sharpe
