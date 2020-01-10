import re
import os
import pandas as pd
import difflib
from bs4 import BeautifulSoup
from distutils.util import strtobool

def extract_paragraphs(xml_path):
    with open(xml_path, 'r') as xml_file:
        xml_content = xml_file.read()
    soup = BeautifulSoup(xml_content, 'lxml')
    return soup.find_all('p')

def split_to_words_and_values(paragraph):
    saids = [(said.get_text(strip=True).split(), said['direct']) for said in paragraph.find_all('said')]
    words = []
    for word_list, value in saids:
        for word in word_list:
            words.append((word, value))
    return words

def check_identity(annotated, baseline, par_id):
    if annotated == baseline:
        return True
    else:
        matcher = difflib.SequenceMatcher(None, annotated, baseline)
        with open('mismatched.txt', 'a') as mismatched_file:
            mismatched_file.write(f'\n========== Mismatched in paragraph {par_id} ==========\n')
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag != 'equal':
                    mismatched_file.write("%7s annotated[%d:%d] (%s) baseline[%d:%d] (%s)\n" % (tag, i1, i2, annotated[i1:i2], j1, j2, baseline[j1:j2]))
        return False

def count_values(annotated_paragraphs, baseline_paragraphs):
    tp, tn, fp, fn = 0, 0, 0, 0
    zipped_p = zip(annotated_paragraphs, baseline_paragraphs)
    for ann_p, base_p in zipped_p:
        if ann_p['n'] == base_p['n']:
            annotated = split_to_words_and_values(paragraph=ann_p)
            baseline = split_to_words_and_values(paragraph=base_p)
            if check_identity(annotated=[i[0] for i in annotated], baseline=[i[0] for i in baseline], par_id=ann_p['n']):
                for a, b in zip(annotated, baseline):
                    ann_value = strtobool(a[1])
                    base_value = strtobool(b[1])
                    if ann_value == True and base_value == True:
                        tp += 1
                    elif ann_value == False and base_value == False:
                        tn += 1
                    elif ann_value == False and base_value == True:
                        fp += 1
                    else:
                        fn += 1        
        else:
            raise NameError('Paragraphs ID\'s doesn\'t match.')
    N = tp + tn + fp + fn
    return tp, tn, fp, fn, N

def calculate_metrics(tp, tn, fp, fn, N):
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    accuracy = (tp + tn) / N
    f1 = 2 * (precision * recall) / (precision + recall)
    return precision, recall, accuracy, f1

def find_baseline(ann_file, baseline_path):
    lang = re.search('annotated_(\w{3})\.xml', ann_file).group(1)
    if lang in os.listdir(baseline_path):
        lang_path = os.path.join(baseline_path, lang)
        base_xml = os.path.join(lang_path, os.listdir(lang_path)[0])
        return lang, base_xml

if __name__ == '__main__':
    annotated_path = os.path.abspath('new/samples_man_annotated/all')
    baseline_path = os.path.abspath('new/samples_baseline')
    df = pd.DataFrame(columns=['precision', 'recall', 'accuracy', 'f1'])
    for ann_file in [f for f in os.listdir(annotated_path) if f != 'annotated_nor.xml']:
        print(f'Processing: {ann_file}')
        lang, base_file = find_baseline(ann_file=ann_file, baseline_path=baseline_path)
        baseline_paragraphs = extract_paragraphs(xml_path=base_file)
        annotated_paragraphs = extract_paragraphs(os.path.join(annotated_path, ann_file))
        tp, tn, fp, fn, N = count_values(annotated_paragraphs=annotated_paragraphs, baseline_paragraphs=baseline_paragraphs)
        df.loc[lang] = calculate_metrics(tp=tp, tn=tn, fp=fp, fn=fn, N=N)
    df.to_csv('precision_recall_output.tsv', sep="\t")
    print('Done.')