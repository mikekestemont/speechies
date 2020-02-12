import re
import os
import csv
import difflib
from bs4 import BeautifulSoup
from distutils.util import strtobool

def extract_paragraphs(xml_path):
    with open(xml_path, 'r') as xml_file:
        xml_content = xml_file.read()
    soup = BeautifulSoup(xml_content, 'lxml')
    return soup.find_all('p')

def split_to_words_and_values(paragraph):
    words = []
    for item in paragraph.contents:
        if item.name == 'said':
            for word in item.text.split():
                words.append((word, True))
        else:
            for word in item.split():
                words.append((word, False))
    return words

def check_identity(annotated, baseline, par_id, lang):
    annotated_tokens = [i[0] for i in annotated]
    baseline_tokens = [i[0] for i in baseline]
    if annotated_tokens == baseline_tokens:
        return annotated, baseline
    else:
        matcher = difflib.SequenceMatcher(None, annotated_tokens, baseline_tokens)
        with open('mismatched.tsv', 'a') as mismatched_file:
            writer = csv.writer(mismatched_file, delimiter='\t')
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag != 'equal':
                    writer.writerow([lang, par_id, f'{i1}:{i2}', annotated_tokens[i1:i2], f'{j1}:{j2}', baseline_tokens[j1:j2]])
        annotated_output = []
        baseline_output = []
        for i, j, n in matcher.get_matching_blocks():
            annotated_output += annotated[i:i+n]
            baseline_output += baseline[j:j+n]
        return annotated, baseline

def count_values(annotated_paragraphs, baseline_paragraphs, lang):
    tp, tn, fp, fn = 0, 0, 0, 0
    zipped_p = zip(annotated_paragraphs, baseline_paragraphs)
    for ann_p, base_p in zipped_p:
        if ann_p['n'] == base_p['n']:
            annotated = split_to_words_and_values(paragraph=ann_p)
            baseline = split_to_words_and_values(paragraph=base_p)
            ann_values, base_values = check_identity(annotated=annotated, baseline=baseline, par_id=ann_p['n'], lang=lang)
            for a, b in zip(ann_values, base_values):
                ann_value = a[1]
                base_value = b[1]
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
    annotated_path = os.path.abspath('new/samples_correct_tei/all')
    baseline_path = os.path.abspath('new/samples_baseline_february')
    
    with open(r'precision_recall_february.tsv', 'w') as precision_recall_file:
        writer = csv.writer(precision_recall_file, delimiter='\t')
        writer.writerow(['lang', 'precision', 'recall', 'accuracy', 'f1'])

    with open(r'mismatched.tsv', 'w') as mismatched_file:
        writer = csv.writer(mismatched_file, delimiter='\t')
        writer.writerow(['lang', 'p_nr', 'ann_pos', 'ann_elem', 'base_pos', 'base_pos'])

    for ann_file in [f for f in os.listdir(annotated_path)]:
        print(f'Processing: {ann_file}')
        lang, base_file = find_baseline(ann_file=ann_file, baseline_path=baseline_path)
        baseline_paragraphs = extract_paragraphs(xml_path=base_file)
        annotated_paragraphs = extract_paragraphs(os.path.join(annotated_path, ann_file))
        tp, tn, fp, fn, N = count_values(annotated_paragraphs=annotated_paragraphs, baseline_paragraphs=baseline_paragraphs, lang=lang)
        precision, recall, accuracy, f1 = calculate_metrics(tp=tp, tn=tn, fp=fp, fn=fn, N=N)
        with open(r'precision_recall_february.tsv', 'a') as precision_recall_file:
            writer = csv.writer(precision_recall_file, delimiter='\t')
            writer.writerow([lang, precision, recall, accuracy, f1])
    print('Done.')