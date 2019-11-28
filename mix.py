import glob
import shutil
import os
import argparse

from toolz.itertoolz import interleave
from sklearn.model_selection import train_test_split as split

from converters import *

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
    args = parser.parse_args()
    print(args)

    try:
        shutil.rmtree(args.split_dir)
    except FileNotFoundError:
        pass
    os.mkdir(args.split_dir)

    sentence_iters = []

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
