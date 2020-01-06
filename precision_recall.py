import re
import os
import pandas as pd
from bs4 import BeautifulSoup
from distutils.util import strtobool

def extract_paragraphs(xml_path):
    with open(xml_path, 'r') as xml_file:
        xml_content = xml_file.read()
    soup = BeautifulSoup(xml_content, 'lxml')
    return soup.find_all('p')

def count_values(true_elements, predicted_elements):
    tp, tn, fp, fn = 0, 0, 0, 0
    zipped_p = zip(true_elements, predicted_elements)
    for true_p, pred_p in zipped_p:
        if true_p['n'] == pred_p['n']:
            true_cond = strtobool(true_p.find('said')['direct'])
            pred_cond = strtobool(pred_p.find('said')['direct'])
            if true_cond == True and pred_cond == True:
                tp += 1
            elif true_cond == False and pred_cond == False:
                tn += 1
            elif true_cond == False and pred_cond == True:
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
    annotated_path = os.path.abspath('new/samples_man_annotated')
    baseline_path = os.path.abspath('new/samples_baseline')
    df = pd.DataFrame(columns=['precision', 'recall', 'accuracy', 'f1'])
    for ann_file in os.listdir(annotated_path):
        print(f'Processing: {ann_file}')
        lang, base_file = find_baseline(ann_file=ann_file, baseline_path=baseline_path)
        baseline_paragraphs = extract_paragraphs(xml_path=base_file)
        annotated_paragraphs = extract_paragraphs(os.path.join(annotated_path, ann_file))
        tp, tn, fp, fn, N = count_values(true_elements=annotated_paragraphs, predicted_elements=baseline_paragraphs)
        df.loc[lang] = calculate_metrics(tp=tp, tn=tn, fp=fp, fn=fn, N=N)
    df.to_excel('precision_recall_output.xlsx')