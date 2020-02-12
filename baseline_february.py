from xml.etree import ElementTree as et
import itertools
import re
import os
# from pdb import set_trace

def baseline(in_file, out_file):
    with open(in_file, 'r', encoding='utf-8') as inf:
        xml = inf.read()
    patterns_quotes = [
        re.compile(r"(\".+?\")"),
        re.compile(r"(“.+?”)"),
        re.compile(r"(„.+?”)"),
        re.compile(r"(„.+?”)"),
        re.compile(r"(».+?«)"),
        re.compile(r"(«.+?»)"),
        re.compile(r"(›.+?‹)"),
        re.compile(r"(›{2}.+?‹{2})"),
        re.compile(r"(„.+?“)"),
        re.compile(r"(\'{2}.+?\'{2})"),
        re.compile(r"(‘{2}.+?‘{2})"),
        re.compile(r"(’{2}.+?’{2})"),
        re.compile(r"(‘.+?’)"),
        re.compile(r"(‘{2}.+?’{2})"),
        re.compile(r"(❝.+?❞)"),
        re.compile(r"(❞.+?❝)"),
        re.compile(r"(〝.+?〞)"),
        re.compile(r"(〞.+?〝)")       
    ]
    pattern_dashes = re.compile(r"^\s*([-֊᠆‐‑⁃﹣－‒–—⁓╌╍⸺⸻⹃〜〰﹘]{1,2}.+?)$")
    pattern_split = re.compile(r"(\s{1}[-֊᠆‐‑⁃﹣－‒–—⁓╌╍⸺⸻⹃〜〰﹘]{1,2}\s{1})|([-֊᠆‐‑⁃﹣－‒–—⁓╌╍⸺⸻⹃〜〰﹘]{1,2}\s{1})|(\s{1}[-֊᠆‐‑⁃﹣－‒–—⁓╌╍⸺⸻⹃〜〰﹘]{1,2})")
    xml_string = et.fromstring(xml)
    tree = et.ElementTree(xml_string)
    root = tree.getroot()
    new_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    for samples in root.iter('samples'):
        samples_n = samples.attrib['n']
        new_content += f'<samples n="{samples_n}">\n'
        # Iterate over samples
        for sample in samples.iter('sample'):
            new_content += '<sample>'
            # Iterate over paragraphs
            for paragraph in sample.iter('p'):
                paragraph_n = paragraph.attrib['n']
                if paragraph.text == None:
                    continue
                new_content += f'<p n="{paragraph_n}">'
                p_content = paragraph.text.strip()
                match_dashes = re.match(pattern_dashes, p_content)
                matches_quotes = [bool(re.search(pattern, p_content)) for pattern in patterns_quotes]
                saids = []
                if match_dashes != None:
                    p_dialog = match_dashes.group()
                    p_dialog_splitted = [i for i in re.split(pattern_split, p_dialog) if i != '' and i != None]
                    if len(p_dialog_splitted) < 2:
                        saids = p_dialog_splitted
                    elif len(p_dialog_splitted) == 2:
                        saids = ["".join(p_dialog_splitted)]
                    else:
                        for i in range(1, len(p_dialog_splitted), 4):
                            try:
                                saids.append("".join([
                                    p_dialog_splitted[i-1],
                                    p_dialog_splitted[i],
                                    p_dialog_splitted[i+1]
                                ]).strip())
                            except IndexError:
                                saids.append("".join([
                                p_dialog_splitted[i-1],
                                p_dialog_splitted[i]
                                ]).strip())
                elif any(matches_quotes):
                    if '»' in p_content and '«' in p_content and p_content.index('»') < p_content.index('«'):
                        pattern = patterns_quotes[4]
                    elif '»' in p_content and '«' in p_content and p_content.index('»') > p_content.index('«'):
                        pattern = patterns_quotes[5]
                    else:
                    # get first matching pattern
                        pattern = patterns_quotes[matches_quotes.index(True)]
                    for m in re.finditer(pattern, p_content):
                        saids.append(m.group())
                else:
                    new_content += p_content + '</p>\n'
                    continue
                match_hits = []
                for said in saids:
                    match = re.search(re.escape(said), p_content)
                    match_hits.append([match.start(), match.end()])
                pos = 0
                for i, (start, end) in enumerate(match_hits, 1):
                    if start == 0 and pos == 0 and end < len(p_content) - 1:
                        new_content += '<said>' + p_content[start:end] + '</said>'
                        pos = end                    
                    else:
                        new_content += p_content[pos:start]
                        new_content += '<said>' + p_content[start:end] + '</said>'
                        pos = end
                    if i == len(match_hits) and len(p_content) > end:
                        new_content += p_content[end:]
                new_content += '</p>\n'
            new_content += '</sample>\n'
        new_content += '</samples>'
        # Save a file
        with open(out_file, 'w', encoding='utf-8') as ouf:
            ouf.write(new_content)

if __name__ == '__main__':
    samples_path = os.path.abspath('new/eltec_samples/')
    baseline_path = os.path.join(os.getcwd(), 'new/samples_baseline_february')
    if not os.path.exists(baseline_path):
        os.makedirs(baseline_path)
    eltec_langs = os.listdir(samples_path)
    for eltec_lang in eltec_langs:
        if eltec_lang.startswith('.'):
            continue
        eltec_path = os.path.join(samples_path, eltec_lang)
        eltec_xmls = os.listdir(eltec_path)
        baseline_lang = os.path.join(baseline_path, eltec_lang)
        if not os.path.exists(baseline_lang):
            os.makedirs(baseline_lang)
        for eltec_xml in eltec_xmls:
            eltec_xml_path = os.path.join(eltec_path, eltec_xml)
            baseline_out = os.path.join(baseline_lang, f'base_{eltec_xml}')
            print(f'Processing file: {eltec_xml}')
            baseline(in_file=eltec_xml_path, out_file=baseline_out)
    print('Done.')












