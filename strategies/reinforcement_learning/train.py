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
    show_eval_result,
    switch_k_backend_device
)


def main(
    stock,
    window_size,
    batch_size,
    ep_count,
    ep_start,
    train,
    train_start,
    train_end,
    validate,
    validate_start,
    validate_end,
    test,
    test_start,
    test_end,
    strategy='t-dqn',
    model_name='model_debug',
    pretrained=False,
    pretrained_model_name=None,
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
    pretrained_model_name = pretrained_model_name or (f'{model_name}_{ep_start-1}' if pretrained else None)
    agent = Agent(window_size,
                  strategy=strategy,
                  pretrained=pretrained,
                  model_name=model_name,
                  pretrained_model_name=pretrained_model_name)

    if train:
        train_data = get_stock_data(stock, train_start, train_end)
        for episode in range(ep_start, ep_start + ep_count):
            train_result = train_model(agent,
                                       episode,
                                       train_data,
                                       ep_count=ep_count,
                                       batch_size=batch_size,
                                       window_size=window_size)
            show_train_result(train_result)

    if validate:
        validate_data = get_stock_data(stock, validate_start, validate_end)
        validate_result = evaluate_model(agent, validate_data, window_size, debug)
        show_eval_result(validate_result)

    if test:
        test_data = get_stock_data(stock, test_start, test_end)
        test_result = evaluate_model(agent, test_data, window_size, debug)
        show_eval_result(test_result)


if __name__ == "__main__":

    stock = 'SPY'

    train = False
    train_start = datetime.date(2010, 1, 1)
    train_end = datetime.date(2017, 12, 31)
    validate = True
    validate_start = datetime.date(2018, 1, 1)
    validate_end = datetime.date(2018, 12, 31)
    test = False
    test_start = datetime.date(2019, 1, 1)
    test_end = datetime.date(2019, 12, 31)

    strategy = 'dqn'
    window_size = 10
    batch_size = 20
    ep_count = 20
    ep_start = 3
    pretrained = True
    model_name = 'model_debug'
    pretrained_model_name = 'model_debug_1'
    debug = True

    coloredlogs.install(level="DEBUG")
    switch_k_backend_device()

    main(stock,
         window_size,
         batch_size,
         ep_count,
         ep_start,
         train,
         train_start,
         train_end,
         validate,
         validate_start,
         validate_end,
         test,
         test_start,
         test_end,
         strategy=strategy,
         model_name=model_name,
         pretrained=pretrained,
         pretrained_model_name=pretrained_model_name,
         debug=debug)
