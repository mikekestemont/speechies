import glob
import re

def extract_ds_from_vrt (in_path, header = True):
    words = []
    with open (in_path, encoding = 'utf8') as fin:
        if header:
            fin.readline ()
        for line in fin:
            els = line.strip ('\n').split ('\t')
            word, isDirect = els[:2]
            words.append ((word, int (isDirect)))
    return words

def words2xml (words):
    ds = False
    text = []
    region = []
    for word in words:
        if word[1] != ds:
            if region:
                text.append ('<said direct="%s">%s</said>' % ('true' if ds else 'false', ' '.join (region)))
            region = []
        region.append (word[0])
        ds = word[1]
    if region:
        text.append ('<said direct="%s">%s</said>' % ('true' if ds else 'false', ' '.join (region)))
    return ''.join (text)

def vrt2eltec_light (in_path, out_path):

    '''converts VRT data with 'Gutenberg-Cor' structure to the 'eltec_light' XML format'''

    words = extract_ds_from_vrt (in_path)
    text = words2xml (words)
    with open (out_path, 'w', encoding = 'utf8') as fout:
        fout.write ('<?xml version="1.0" encoding="utf-8"?>\n<doc>\n')
        fout.write (text)
        fout.write ('\n</doc>')

def xml2eltec_light (in_path, out_path):

    '''converts XML data in 'small-en' format to the 'eltec_light' XML format'''

    DS_TAG = 'said'
    DS_TAG_OPEN = 'said direct="%s"'
    chapters = []
    with open (in_path, encoding = 'utf8') as fin:
        text = fin.read ()
    for chapter in re.findall ('<chapter>.*?</chapter>', text, re.S):
        chapter = re.sub ('<quote.*?>', r'<%s>' % DS_TAG_OPEN % 'true', chapter)
        chapter = re.sub ('</quote>', '</%s>' % DS_TAG, chapter)
        chapter = re.sub ('<(?!/?%s).*?>' % DS_TAG, '', chapter)
        pos = 0
        updated_chapter = ''
        not_directs = []
        for match in re.finditer ('<%s.*?>.*?</%s>' % (DS_TAG, DS_TAG), chapter):
            not_directs.append ((pos, match.start (), match.end ()))
            pos = match.end ()
        for nds in not_directs:
            tmp = chapter[nds[0]:nds[1]]
            if tmp.strip ():
                updated_chapter += '<%s>' % DS_TAG_OPEN % 'true' + tmp + '</%s>' % DS_TAG
            else:
                updated_chapter += tmp
            updated_chapter += chapter[nds[1]:nds[2]]
        if chapter[not_directs[-1][2]:].strip ():
            updated_chapter +=  '<%s>' % DS_TAG_OPEN % 'false' + chapter[not_directs[-1][2]:] + '</%s>' % DS_TAG
        chapters.append (updated_chapter)
    with open (out_path, 'w', encoding = 'utf8') as fout:
        fout.write ('<?xml version="1.0" encoding="utf-8"?>\n<doc>\n')
        fout.write ('\n\t'.join (chapters))
        fout.write ('\n</doc>')

def vrt2bert (in_path, header = True):

    '''INPUT: file in a vrt format (Gutenbert-Cor strucutre)
    OUTPUT: list of tokens with DS annotation (tuple: (word, label))'''

    tokens = []
    with open (in_path, encoding = 'utf8') as fin:
        if header:
            fin.readline ()
        for line in fin:
            els = line.strip ('\n').split ('\t')
            if int (els[1]) == 0 :
                els[1] = 'O'
            elif int (els[1]) == 1:
                els[1] = 'I'
            if tokens and els[4] == 'start':
                tokens.append ('')
            tokens.append (els[:2])

    return tokens

def write_to_bert_input_file (out_path, tokens):

    '''saves list of tokens (tuple (word, lable)) into a file'''

    with open (out_path, 'w', encoding = 'utf8') as fout:
        for t in tokens:
            fout.write (' '.join (t) + '\n')

if __name__ == '__main__':
tokens = []
fnames = glob.glob ('gutenberg_cor-de/*') + glob.glob ('kern_rich-de/*')
for fname in fnames:
    try:
        tokens += vrt2bert (fname)
    except:
        print ('Failed:', fname)
    writeToFile ('deBert.vrt', tokens)
