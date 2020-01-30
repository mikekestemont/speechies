# Speechies pipeline

Following [this solution](https://huggingface.co/transformers/examples.html#named-entity-recognition)

## Preparing data


## Necessary installations

### Setting up virtual environment
Prepare your virtual environment
* Start by creating one, e.g. if you want the name to be bertner:
`virtualenv -p /usr/local/bin/python3.8 bertner`
* Activate environment by typing:
`source /srv/speechies/bertner/bin/activate`
* Install required packages:
```
pip install numpy
pip install torch
pip install seqeval
pip install tensorboardX
pip install tqdm
pip install transformers

```

## Running the experiment
### Setup
* Create an experiment folder, e.g. *serbian_test*, *1/2data_test*.
* The folder should contain following files:
   * train.txt
   * test.txt
   * dev.txt
   * labels.txt
   * run_ner.py
   * utils_ner.py
* Start a new tmux session, e.g. if session name is *serbian_test*
`tmux new -s serbian_test`
* Activate virtual environment	
`source /srv/speechies/bertner/bin/activate`

### Executing experiment

If previous steps are completed, type:
```
export MAX_LENGTH=256
export BERT_MODEL=bert-base-multilingual-cased
export OUTPUT_DIR=model-with-serbian
export BATCH_SIZE=32
export NUM_EPOCHS=3
export SAVE_STEPS=750
export SEED=1


python run_ner.py --data_dir ./ \
--model_type bert \
--labels ./labels.txt \
--model_name_or_path $BERT_MODEL \
--output_dir $OUTPUT_DIR \
--max_seq_length  $MAX_LENGTH \
--num_train_epochs $NUM_EPOCHS \
--per_gpu_train_batch_size $BATCH_SIZE \
--save_steps $SAVE_STEPS \
--seed $SEED \
--do_train \
--do_eval \
--do_predict
```
Once you see a slider with progress in training of epoch, detach your tmux session by pressing **ctrl + b** and then **d**

## Checking results

You can check the progress / final state of experiment by rejoining your session:
`tmux a -t serbian_test`

If the experiment reached its end, you should see report like this, with different values:
```
f1 = 0.9125053350405463
loss = 0.17977334592478272
precision = 0.8968120805369127
recall = 0.9287576020851434
```




