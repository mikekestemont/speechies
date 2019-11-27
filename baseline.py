from xml.etree import ElementTree as et
import itertools
import re
import os

def baseline(in_file, out_file):
    with open(in_file, 'r', encoding='utf-8') as inf:
        xml = inf.read()
    pattern = re.compile(r'^([„\"«‹„‟‛”’"❛❜❝❞❮⹂〞〟＂].*?[”\"»›“‘❯〝‟‛”’"❛❜❝❞])|([‒–—―⁓].*?[‒–—―⁓])', flags=re.MULTILINE)
    tree = et.ElementTree(et.fromstring(xml))
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
                new_content += f'<p n="{paragraph_n}">'
                p_content = paragraph.text.strip()
                # Find matches
                if re.match(pattern, p_content):
                    for match in re.finditer(pattern, p_content):
                        if match.start() == 0 and match.end() < len(p_content) - 1:
                            tagged_line = f'<said direct=True>{match.group()}</said><said direct=False>{p_content[match.end():]}</said></p>\n'
                            new_content += tagged_line
                        elif match.start() > 0 and match.end() < len(p_content) - 1:
                            tagged_line = f'<said direct=False>{p_content[:match.start()]}</said><said direct=True>{match.group()}</said><said direct=False>{p_content[match.end():]}</said></p>\n'
                            new_content += tagged_line
                        elif match.start() > 0 and match.end() == len(p_content) - 1:
                            tagged_line = f'<said direct=False>{p_content[:match.start()]}</said><said direct=True>{match.group()}</said></p>\n'
                            new_content += tagged_line
                        elif match.start() == 0 and match.end() == len(p_content) - 1:
                            tagged_line = f'<said direct=True>{match.group()}</said></p>\n'
                            new_content += tagged_line
                        else:
                            tagged_line = f'<said direct=False>{p_content}</said></p>\n'
                            new_content += tagged_line    
                else:
                    tagged_line = f'<said direct=False>{p_content}</said></p>\n'
                    new_content += tagged_line                   
            new_content += '</sample>'
        new_content += '</samples>'
        # Save a file
        with open(out_file, 'w', encoding='utf-8') as ouf:
            ouf.write(new_content)
        print(new_content)

if __name__ == '__main__':
    samples_path = os.path.abspath('samples_of_eltec/samples')
    example_file = os.path.join(samples_path, 'eng/eng1.xml')
    baseline(in_file=example_file, out_file='sample.xml')
