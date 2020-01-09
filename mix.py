import glob
import shutil
import os
import argparse
import random

from toolz.itertoolz import interleave
from sklearn.model_selection import train_test_split as split

from converters import *

def split_paragraphs (paragraphs, train_ratio, random_state):
    assert train_ratio > 0 and train_ratio < 1
    random.seed (random_state)
    random.shuffle (paragraphs)
    size = sum ([len (par) for par in paragraphs])
    train_size = 0
    dev_size = 0
    ind = 0
    while train_size < size * train_ratio:
        train_size += len (paragraphs[ind])
        ind += 1
    train = paragraphs[:ind]
    while dev_size < size * (1 - train_ratio) / 2:
        dev_size += len (paragraphs[ind])
        ind += 1
    dev = paragraphs[len (train):ind]
    test = paragraphs[ind:]

    return train, dev, test

def get_sentences (paragraphs):

    sentences = []
    for paragraph in paragraphs:
        for sent in paragraph:
            sentences.append ('\n'.join([' '.join(token) for token in sent]) + '\n')

    return sentences


def main():
    parser = argparse.ArgumentParser(description='Splits available (multilingual) sentences in train-dev-test')
    parser.add_argument('--input_dir', type=str,
                        default='samples_man_annotated',
                        help='location of the annotated Eltec files')
    parser.add_argument('--split_dir', type=str,
                        default='multilingual_splits',
                        help='location of the train-dev-test files')
    parser.add_argument('--train_prop', type=float,
                        default=.8,
                        help='Proportion of training items (dev and test are equal-size)')
    parser.add_argument('--seed', type=int,
                        default=43438,
                        help='Random seed')
    parser.add_argument('--paragraphs',
                        action = 'store_true',
                        help='')
    args = parser.parse_args()
    print(args)

    try:
        shutil.rmtree(args.split_dir)
    except FileNotFoundError:
        pass
    os.mkdir(args.split_dir)

    sentence_iters = []
    paragraphs = []

    if args.paragraphs:
        for filename in glob.iglob(f'{args.input_dir}/**/*.xml', recursive=True):
            print (filename)
            paragraphs += annotated2paragraphs (filename)
        train, dev, test = split_paragraphs (paragraphs,
                                        train_ratio = args.train_prop,
                                        random_state = args.seed)
        train = get_sentences (train)
        dev = get_sentences (dev)
        test = get_sentences (test)
    else:
        for filename in glob.iglob(f'{args.input_dir}/**/*.xml', recursive=True):
            print(filename)
            sentences = annotated2sentences(filename)
            sentence_iters.append(sentences)

        mixed_sentences = interleave(sentence_iters)

        formatted_sentences = []
        for sentence in mixed_sentences:
            s = '\n'.join([' '.join(token) for token in sentence]) + '\n'
            formatted_sentences.append(s)

        # for sentence in formatted_sentences:
            # print(sentence)

        train, rest = split(formatted_sentences,
                            train_size=args.train_prop,
                            shuffle=True,
                            random_state=args.seed)
        dev, test = split(rest,
                          train_size=0.5,
                          shuffle=True,
                          random_state=args.seed)

    print(f'# train items: {len(train)}')
    print(f'# dev test: {len(dev)}')
    print(f'# test items: {len(test)}')

    for items in ('train', 'dev', 'test'):
        with open(os.sep.join((args.split_dir, items + '.txt')), 'w', encoding = 'utf8') as f:
            f.write('\n'.join(eval(items)))


if __name__ == '__main__':
    main()
