"""
Script for training Stock Trading Bot.

Usage:
  train.py <train-stock> <val-stock> [--strategy=<strategy>]
    [--window-size=<window-size>] [--batch-size=<batch-size>]
    [--episode-count=<episode-count>] [--model-name=<model-name>]
    [--pretrained] [--debug]

Options:
  --strategy=<strategy>             Q-learning strategy to use for training the network. Options:
                                      `dqn` i.e. Vanilla DQN,
                                      `t-dqn` i.e. DQN with fixed target distribution,
                                      `double-dqn` i.e. DQN with separate network for value estimation. [default: t-dqn]
  --window-size=<window-size>       Size of the n-day window stock data representation
                                    used as the feature vector. [default: 10]
  --batch-size=<batch-size>         Number of samples to train on in one mini-batch
                                    during training. [default: 32]
  --episode-count=<episode-count>   Number of trading episodes to use for training. [default: 50]
  --model-name=<model-name>         Name of the pretrained model to use. [default: model_debug]
  --pretrained                      Specifies whether to continue training a previously
                                    trained model (reads `model-name`).
  --debug                           Specifies whether to use verbose logs during eval operation.
"""

import datetime
import coloredlogs

from strategies.reinforcement_learning.agent import Agent
from strategies.reinforcement_learning.methods import train_model, evaluate_model
from strategies.reinforcement_learning.ops import (
    get_stock_data,
    show_train_result,
    switch_k_backend_device
)


def main(
    stock,
    window_size,
    batch_size,
    ep_count,
    train_start,
    train_end,
    val_start,
    val_end,
    strategy='t-dqn',
    model_name='model_debug',
    pretrained=False,
    debug=False
):
    """ Trains the stock trading bot using Deep Q-Learning.
    Please see https://arxiv.org/abs/1312.5602 for more details.

    For each episode, we train the Agent using the entire training data set.
    We divide each episode (entire training data) into batches.
    For each training sample in a batch, Agent observes state, act, get a reward.
    Each training sample play is memorized. We calibrate Agent parameters at end of each batch.

    Args: [python train.py --help]
    """
    agent = Agent(window_size, strategy=strategy, pretrained=pretrained, model_name=model_name)

    train_data = get_stock_data(stock, train_start, train_end)
    val_data = get_stock_data(stock, val_start, val_end)

    initial_offset = val_data[1] - val_data[0]

    for episode in range(1, ep_count + 1):
        train_result = train_model(agent, episode, train_data, ep_count=ep_count,
                                   batch_size=batch_size, window_size=window_size)
        val_result, _ = evaluate_model(agent, val_data, window_size, debug)
        show_train_result(train_result, val_result, initial_offset)


if __name__ == "__main__":

    stock = 'SPY'
    train_start = datetime.date(2010, 1, 1)
    train_end = datetime.date(2017, 12, 31)
    val_start = datetime.date(2018, 1, 1)
    val_end = datetime.date(2018, 12, 31)
    strategy = 'dqn'
    window_size = 10
    batch_size = 20
    ep_count = 20
    model_name = 'model_debug'
    pretrained = True
    debug = True

    coloredlogs.install(level="DEBUG")
    switch_k_backend_device()

    main(stock,
         window_size,
         batch_size,
         ep_count,
         train_start,
         train_end,
         val_start,
         val_end,
         strategy=strategy,
         model_name=model_name,
         pretrained=pretrained,
         debug=debug)
