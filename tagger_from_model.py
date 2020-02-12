# coding: utf-8
# importing necessary libraries
from __future__ import absolute_import, division, print_function

import argparse
import glob
import logging
import os
import random

import numpy as np
import torch
from seqeval.metrics import precision_score, recall_score, f1_score
from tensorboardX import SummaryWriter
from torch.nn import CrossEntropyLoss
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler, TensorDataset
from torch.utils.data.distributed import DistributedSampler
from tqdm import tqdm, trange
from utils_ner import convert_examples_to_features, get_labels, read_examples_from_file

from transformers import AdamW
from transformers import WEIGHTS_NAME, BertConfig, BertForTokenClassification, BertTokenizer

# setting up pre-trained model to be used
MODEL_CLASSES = {
    "bert": (BertConfig, BertForTokenClassification, BertTokenizer),
}
config_class, model_class, tokenizer_class = MODEL_CLASSES['bert']
# location of the model of choice
model_dir = 'model/'
model = model_class.from_pretrained(model_dir)
case = False
tokenizer = tokenizer_class.from_pretrained(model_dir, do_lower_case=case)
device = 'cpu'
model.to(device)

# setting the folder for possible whole directory tagging
files_dir = 'data/'

# getting labels
labels = get_labels('labels.txt')
pad_token_label_id = CrossEntropyLoss().ignore_index

# reading examples
examples = read_examples_from_file('.', 'test')
features = convert_examples_to_features(examples, labels, 256, tokenizer, cls_token_at_end=False, cls_token=tokenizer.cls_token, cls_token_segment_id=0, sep_token=tokenizer.sep_token, sep_token_extra=False, pad_on_left=False, pad_token=tokenizer.convert_tokens_to_ids([tokenizer.pad_token])[0], pad_token_segment_id=0, pad_token_label_id=pad_token_label_id)
all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
all_input_mask = torch.tensor([f.input_mask for f in features], dtype=torch.long)
all_segment_ids = torch.tensor([f.segment_ids for f in features], dtype=torch.long)
all_label_ids = torch.tensor([f.label_ids for f in features], dtype=torch.long)
dataset = TensorDataset(all_input_ids, all_input_mask, all_segment_ids, all_label_ids)

# setting eval (predictions) dataset parameters
eval_dataset = dataset
per_gpu_eval_batch_size = 32
n_gpu = 0
eval_batch_size = per_gpu_eval_batch_size * max(1, n_gpu)
eval_sampler = SequentialSampler(eval_dataset)
eval_dataloader = DataLoader(eval_dataset, sampler=eval_sampler, batch_size=eval_batch_size)
eval_loss = 0.0
nb_eval_steps = 0
preds = None
out_label_ids = None
model.eval()
model_type = 'bert'
counter = 0

# creating predictions
for batch in tqdm(eval_dataloader, desc="Evaluating"):
        batch = tuple(t.to(device) for t in batch)

        with torch.no_grad():
            inputs = {"input_ids": batch[0],
                      "attention_mask": batch[1],
                      "labels": batch[3]}
            if model_type != "distilbert":
                inputs["token_type_ids"] = batch[2] if model_type in ["bert", "xlnet"] else None  # XLM and RoBERTa don"t use segment_ids
            outputs = model(**inputs)
            tmp_eval_loss, logits = outputs[:2]

            if n_gpu > 1:
                tmp_eval_loss = tmp_eval_loss.mean()  # mean() to average on multi-gpu parallel evaluating

            eval_loss += tmp_eval_loss.item()
        nb_eval_steps += 1
        if preds is None:
            preds = logits.detach().cpu().numpy()
            out_label_ids = inputs["labels"].detach().cpu().numpy()
        else:
            preds = np.append(preds, logits.detach().cpu().numpy(), axis=0)
            out_label_ids = np.append(out_label_ids, inputs["labels"].detach().cpu().numpy(), axis=0)
	 # for testing
        counter += 1
        if counter > 3:
            break

preds = np.argmax(preds, axis=2)
label_map = {i: label for i, label in enumerate(labels)}
out_label_list = [[] for _ in range(out_label_ids.shape[0])]
preds_list = [[] for _ in range(out_label_ids.shape[0])]
for i in range(out_label_ids.shape[0]):
    for j in range(out_label_ids.shape[1]):
        if out_label_ids[i, j] != pad_token_label_id:
            out_label_list[i].append(label_map[out_label_ids[i][j]])
            preds_list[i].append(label_map[preds[i][j]])
predictions = preds_list