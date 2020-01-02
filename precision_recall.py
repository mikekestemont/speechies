import os
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

if __name__ == '__main__':
    man_annotated_path = os.path.abspath('samples_man_annotated/joanna/annotated_deu/annotated_base_deu1.xml')
    man_annotated_paragraphs = extract_paragraphs(man_annotated_path)
    baseline_path = os.path.abspath('samples_baseline/deu/base_deu1.xml')
    baseline_paragraphs = extract_paragraphs(baseline_path)
    tp, tn, fp, fn, N = count_values(true_elements=man_annotated_paragraphs, predicted_elements=baseline_paragraphs)
    precision, recall, accuracy, f1 = calculate_metrics(tp=tp, tn=tn, fp=fp, fn=fn, N=N)
    print('Precision:', precision)
    print('Recall:', recall)
    print('Accuracy:', accuracy)
    print('F1:', f1)