from xml.etree import ElementTree as et
import itertools
import re
import os

def baseline(in_file, out_file):
    with open(in_file, 'r', encoding='utf-8') as inf:
        xml = inf.read()
    patterns = [
        re.compile(r"^\s*([\"].*?[\"])", flags=re.MULTILINE),
        re.compile(r"^\s*([\'].*?[\'])", flags=re.MULTILINE),
        re.compile(r"^\s*([-]+.*?[-]+)", flags=re.MULTILINE),
        re.compile(r"^\s*([—]+.*?[—]+)", flags=re.MULTILINE),
        re.compile(r"^\s*([—]+.*?[—]+)", flags=re.MULTILINE),
        re.compile(r"^\s*([-]+.*?)$", flags=re.MULTILINE),
        re.compile(r"^\s*([—]+.*?)$", flags=re.MULTILINE),
        re.compile(r"^\s*([—]+.*?)$", flags=re.MULTILINE),
        re.compile(r"^\s*([-]+.*?)\n", flags=re.MULTILINE),
        re.compile(r"^\s*([—]+.*?)\n", flags=re.MULTILINE),
        re.compile(r"^\s*([—]+.*?)\n", flags=re.MULTILINE),
        re.compile(r"^\s*([„].*?[”])", flags=re.MULTILINE),
        re.compile(r"^\s*([«].*?[»])", flags=re.MULTILINE),
        re.compile(r"^\s*([»].*?[«])", flags=re.MULTILINE),
        re.compile(r"^\s*([›].*?[‹])", flags=re.MULTILINE),
        re.compile(r"^\s*([“].*?[”])", flags=re.MULTILINE),
        re.compile(r"^\s*([„].*?[“])", flags=re.MULTILINE),
        re.compile(r"^\s*([«].*?)$", flags=re.MULTILINE),
        re.compile(r"^\s*([»].*?)$", flags=re.MULTILINE),
        re.compile(r"^\s*([«].*?)\n", flags=re.MULTILINE),
        re.compile(r"^\s*([»].*?)\n", flags=re.MULTILINE),
        re.compile(r"([-]+.*?)$", flags=re.MULTILINE),
        re.compile(r"([—]+.*?)$", flags=re.MULTILINE),
        re.compile(r"([—]+.*?)$", flags=re.MULTILINE),
    ]
    
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
                # Find matches
                matches = [re.match(pattern, p_content) for pattern in patterns]
                if any(matches):
                    # get first matching pattern
                    pattern = patterns[next((i for i, j in enumerate(matches) if j), None)]
                    for match in re.finditer(pattern, p_content):
                        if match.start() == 0 and match.end() < len(p_content) - 1:
                            tagged_line = f'<said direct="true">{match.group()}</said><said direct="false">{p_content[match.end():]}</said></p>\n'
                            new_content += tagged_line
                            continue
                        elif match.start() > 0 and match.end() < len(p_content) - 1:
                            tagged_line = f'<said direct="false">{p_content[:match.start()]}</said><said direct="true">{match.group()}</said><said direct="false">{p_content[match.end():]}</said></p>\n'
                            new_content += tagged_line
                            continue
                        elif match.start() > 0 and match.end() == len(p_content) - 1:
                            tagged_line = f'<said direct="false">{p_content[:match.start()]}</said><said direct="true">{match.group()}</said></p>\n'
                            new_content += tagged_line
                            continue
                        elif match.start() == 0 and match.end() == len(p_content) - 1:
                            tagged_line = f'<said direct="true">{match.group()}</said></p>\n'
                            new_content += tagged_line
                            continue
                        else:
                            tagged_line = f'<said direct="false">{p_content}</said></p>\n'
                            new_content += tagged_line    
                            continue
                else:
                    tagged_line = f'<said direct="false">{p_content}</said></p>\n'
                    new_content += tagged_line  
         
            new_content += '</sample>\n'
        new_content += '</samples>'
        # Save a file
        with open(out_file, 'w', encoding='utf-8') as ouf:
            ouf.write(new_content)

if __name__ == '__main__':
    samples_path = os.path.abspath('samples_of_eltec/samples')
    baseline_path = os.path.join(os.getcwd(), 'samples_baseline')
    if not os.path.exists(baseline_path):
        os.makedirs(baseline_path)
    eltec_langs = os.listdir(samples_path)
    for eltec_lang in eltec_langs:
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
