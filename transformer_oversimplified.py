"""
Super simplified example for illustrating Transformer.
1. We showed only one Encoder and one Decoder.
2. We did not implement Positional Encoding.
3. We ignored Multi-Head attention. In real practice, it's usually an ensemble of h self attention in one Encoder / Decoder.
4. We ignored Residual Connection and Layer Normalization.
5. We assume the input word embeddings are given. Reduced to dimension of 3 for illustration.
6. We assume the Query / Key / Value weight matrices are given. Reduced to dimension of 3 for illustration.
7. We assume the parameters of Feed Forward Neural Network in Encoder / Decoder are given.
8. We ignored the Final Linear Layer and Softmax Layer.
"""

import numpy as np
from scipy.special import softmax
from pprint import pprint

WEIGHTS_QUERY = np.array([
    [1, 2, 3],
    [1, 2, 3],
    [1, 2, 3],
])

WEIGHTS_KEY = np.array([
    [1, 2, 3],
    [1, 2, 3],
    [1, 2, 3],
])

WEIGHTS_VALUE = np.array([
    [1, 2, 3],
    [1, 2, 3],
    [1, 2, 3],
])

INPUT_EMBEDDING = np.array([
    [0.1, 0.2, 0.3],
    [0.3, 0.3, 0.3],
])

OUTPUT_EMBEDDING = np.array([
    [0.1, 0.2, 0.3],
    [0.3, 0.3, 0.3],
])

WEIGHTS_FFN_L1 = np.array([
    [0.2, 1, 1],
    [1, 1, 0.1],
    [1, 0.6, 1],
])

WEIGHTS_FFN_L2 = np.array([
    [0.2, 1, 0.4],
    [0.7, 0.3, 0.1],
    [1, 0.6, 1],
])


def self_attention(x, w_q, w_k, w_v):
    # encoder_decoder_attention is a generalization of self_attention from implementation perspective
    z = encoder_decoder_attention(x, x, w_q, w_k, w_v)
    return z


def feed_forward_neural_network(z):
    print('Input:')
    pprint(z)

    # FFN Hidden layer uses ReLU activation function
    z1 = np.maximum(np.matmul(z, WEIGHTS_FFN_L1), 0)

    # FFN Output layer uses linear unit
    r = np.matmul(z1, WEIGHTS_FFN_L2)
    print('Output:')
    pprint(r)

    return r


def encoder_decoder_attention(x_encoder, x_decoder, w_q, w_k, w_v):
    # Calculate Query / Key / Value for each inputs.
    q = np.matmul(x_decoder, w_q)
    k = np.matmul(x_encoder, w_k)
    v = np.matmul(x_encoder, w_v)

    # Calculate scores by matching Query with Key across inputs. Higher score indicates better matching.
    score = np.matmul(q, k.T)
    print('Score:')
    pprint(score)

    # Scale scores, dividing by Key dimension
    num_row, num_col = k.shape
    scaled_score = score / np.sqrt(num_col)

    # Softmax scaled scores to get probability of each Query-Key pair for a given input.
    p = softmax(scaled_score, axis=1)
    print('Probability:')
    pprint(p)

    # Output Value for a given input, weighted by above probability
    z = np.matmul(p, v)
    print('Output:')
    pprint(z)

    return z


def encoder(x):
    print('Self Attention:')
    z = self_attention(x, WEIGHTS_QUERY, WEIGHTS_KEY, WEIGHTS_VALUE)
    print('Feed Forward Neural Network:')
    r = feed_forward_neural_network(z)
    return r


def decoder(x, x_encoder):
    print('Self Attention:')
    x_decoder = self_attention(x, WEIGHTS_QUERY, WEIGHTS_KEY, WEIGHTS_VALUE)
    print('Encoder Decoder Attention:')
    z = encoder_decoder_attention(x_encoder, x_decoder, WEIGHTS_QUERY, WEIGHTS_KEY, WEIGHTS_VALUE)
    print('Feed Forward Neural Network:')
    r = feed_forward_neural_network(z)
    return r


def transformer(x_input, x_output):
    print('Encoder:')
    x_encoder = encoder(x_input)
    print('Decoder:')
    r = decoder(x_output, x_encoder)

    # TODO: Final Linear and Softmax Layer to project Decoder output to probabilities of known words.
    return r


def main():
    print('Transformer:')
    res = transformer(INPUT_EMBEDDING, OUTPUT_EMBEDDING)
    print('Transformer Output:')
    pprint(res)


if __name__ == '__main__':
    main()
