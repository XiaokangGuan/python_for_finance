import numpy as np
import pandas as pd
from tqdm import tqdm
from .ops import get_state, log_daily_flash, sigmoid, calculate_commission
from utils.performance_evaluation import annualized_return, annualized_volatility, sharpe_ratio

# Logic:
# 1. Take full position every time, i.e. Full long or Full short or Flat.
# 2. Allow Long, Long MV is capped by min(initial capital, portfolio value).
# 3. Allow Short, Short MV is capped by min(initial capital, portfolio value).

def execute_model(agent, data, mode, episode=1, ep_count=100, batch_size=32, window_size=10, train_experience=True, debug=False):
    agent.debug = debug

    # Initial portfolio
    initial_quantity = 0
    initial_mv = 0
    initial_cash = 10000

    data_length = len(data) - 1
    model_loss = []
    history = []

    # Reset starting point
    quantity = initial_quantity
    mv = initial_mv
    cash = initial_cash
    state = get_state(data, 0, window_size + 1, 0.5)

    if mode == 'train':
        iter_range = tqdm(range(data_length), total=data_length, leave=True, desc='Episode {}/{}'.format(episode, ep_count))
    else:
        iter_range = range(data_length)

    for t in iter_range:
        # Select an action
        action = agent.act(state)

        # Full Long: Long amount is capped
        if action == 1:
            action_name = 'Full Long'
            long_mv_cap = min(initial_cash, cash + mv)
            next_quantity = int(long_mv_cap / data[t])
            trade_quantity = next_quantity - quantity
            next_mv = data[t + 1] * next_quantity
            next_cash = cash - data[t] * trade_quantity
            commission = calculate_commission(trade_quantity)
            reward = sigmoid(next_mv + next_cash - mv - cash - commission)

        # Full Short: Short amount is capped
        elif action == 2:
            action_name = 'Full Short'
            short_mv_cap = min(initial_cash, cash + mv)
            next_quantity = - int(short_mv_cap / data[t])
            trade_quantity = next_quantity - quantity
            next_mv = data[t + 1] * next_quantity
            next_cash = cash - data[t] * trade_quantity
            commission = calculate_commission(trade_quantity)
            reward = sigmoid(next_mv + next_cash - mv - cash - commission)

        # Neutral / Flat: Close all stock positions, as we do not bet if uncertain
        else:
            action_name = 'Flat'

            next_quantity = 0
            trade_quantity = next_quantity - quantity
            next_mv = data[t + 1] * next_quantity
            # TODO: Possible to run negative cash?
            next_cash = cash - data[t] * trade_quantity
            commission = calculate_commission(trade_quantity)
            reward = sigmoid(next_mv + next_cash - mv - cash - commission)

        history.append((t, data[t], action_name, mv, cash))
        if debug:
            log_daily_flash(t, action_name, trade_quantity, data[t], quantity, mv, cash, next_quantity, next_mv, next_cash, initial_cash + initial_mv)

        # Memorize
        # Reward is defined as entire portfolio value change from state to next_state,
        # i.e. including both stock MV change (due to action / price change) and cash change.
        done = (t == data_length - 1)
        next_state = get_state(data, t + 1, window_size + 1, sigmoid(next_mv / (next_cash + next_mv)))
        agent.remember(state, action, reward, next_state, done)

        # Train on experience
        if train_experience and len(agent.memory) > batch_size:
            loss = agent.train_experience_replay(batch_size)
            model_loss.append(loss)

        state = next_state
        quantity = next_quantity
        mv = next_mv
        cash = next_cash

    return history, model_loss


def train_model(agent, episode, data, ep_count=100, batch_size=32, window_size=10, debug=False):
    history, model_loss = execute_model(agent,
                                        data,
                                        'train',
                                        episode=episode,
                                        ep_count=ep_count,
                                        batch_size=batch_size,
                                        window_size=window_size,
                                        debug=debug)

    agent.save(episode)
    total_profit = history[-1][3] + history[-1][4] - history[0][3] - history[0][4]
    return episode, ep_count, total_profit, np.mean(np.array(model_loss))


def evaluate_model(agent, start, end, data, batch_size=32, window_size=10, train_in_evaluate=True, debug=False):
    history, model_loss = execute_model(agent,
                                        data,
                                        'evaluate',
                                        batch_size=batch_size,
                                        window_size=window_size,
                                        train_experience=train_in_evaluate,
                                        debug=debug)

    # Metrics
    total_profit = history[-1][3] + history[-1][4] - history[0][3] - history[0][4]
    daily_portfolio = pd.Series([mv + cash for _, _, _, mv, cash in history])
    annual_return = annualized_return(daily_portfolio)
    annual_vol = annualized_volatility(daily_portfolio)
    sharpe = sharpe_ratio(daily_portfolio, risk_free=0.0017625)
    return start, end, total_profit, annual_return, annual_vol, sharpe
