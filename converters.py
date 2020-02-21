import glob
import os
import re
import lxml.etree

from nltk import word_tokenize, sent_tokenize


def get_paragraph_chunks (paragraph):

    def in_said (element):
        return bool (element.xpath ('ancestor::said'))

    def get_node_text (node):
        text = []
        if node.text and node.text.strip ():
            text.append (' '.join (node.text.split ()))
        for child in node.getchildren ():
            if child.tag == 'said':
                break
            text += get_node_text (child)
            if child.tail:
                text.append (' '.join (child.tail.split ()))
        return text

    chunks = []
    chunk = []
    tail = []

    for element in paragraph.iter ():
        if element.tag == 'said':
            if tail:
                chunk += tail
                tail = []
            if chunk:
                chunks.append ((' '.join (chunk), 'O'))
                chunk = []
            chunks.append ((' '.join (get_node_text (element)), 'I'))
            if element.tail:
                tail += element.tail.split ()
        else:
            if in_said (element):
                continue
            if tail:
                chunk += tail
                tail = []
            chunk += get_node_text (element)
            if element.tail:
                chunk += element.tail.split ()
    if chunk:
        chunks.append ((' '.join (chunk), 'O'))

    return chunks

def annotated2sentences(source):
    sentences = []
    if type (source) == str:
        root = lxml.etree.parse(source).getroot()
    else:
        root = source
    text = []
    direct = []
    for paragraph in root.iterfind('.//p'):
        for text, direct in get_paragraph_chunks (paragraph):
            for sent in sent_tokenize(text):
                sentence = []
                for token in word_tokenize(sent):
                    sentence.append((token, direct))
                sentences.append(sentence)
    return sentences

def annotated2paragraphs (path):
    paragraphs = []
    tree = lxml.etree.parse(path)
    for paragraph in tree.iterfind ('//p'):
        paragraphs.append (annotated2sentences (paragraph))

    return paragraphs

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

def tokenize (text):
    text = re.sub (r'[\r\n\t]', ' ', text)
    text = re.sub (r' {2,}', ' ', text)
    return [tok for tok in re.split (r'([^\w-])', text) if tok.strip ()]

def tei2bert (in_path, out_path):
    root = lxml.etree.parse(in_path).getroot()
    paragraphs = []
    for paragraph in root.findall ('.//p', namespaces = root.nsmap):
        text = ' '.join ([t for t in paragraph.itertext ()])
        tokens = tokenize (text)
        paragraphs.append ('\n'.join (tokens))
    with open (out_path, 'w', encoding = 'utf8') as fout:
        fout.write ('\n\n'.join (paragraphs))

def bert2tei (xml_path, bert_path, save = False):

    def find_paragraphs_with_words (text):
        pat = re.compile (r'<p(?:>| [^/]*?>)(.*?)</p>', re.DOTALL)
        paragraphs = []
        position = 0
        for par_match in re.finditer (pat, text):
            paragraph = []
            position = par_match.start ()
            if par_match.group (1) == None or not par_match.group (1).strip ():
                paragraphs.append (paragraph)
                continue
            for word in tokenize (par_match.group (1)):
                word_start = text.find (word, position, position + 50)
                assert word_start != -1
                word_end = word_start + len (word)
                paragraph.append ((word_start, word_end))
                position = word_end
            paragraphs.append (paragraph)

        return paragraphs

    def find_chunks (tokens):

        chunks = []
        cur_label = 'O'
        chunk_start = -1
        for ind, token in enumerate (tokens):
            if cur_label != token[1]:
                if token[1] == 'O':
                    chunks.append ((chunk_start, ind - 1))
                    chunk_start = -1
                else:
                    chunk_start = ind
            cur_label = token[1]
        if chunk_start != -1:
            chunks.append ((chunk_start, len (tokens) - 1))

        return chunks

    bert_paragraphs = []
    with open (bert_path, encoding = 'utf8') as fbert:
        par = []
        for line in fbert:
            if line == '\n':
                if par:
                    bert_paragraphs.append (par)
                    par = []
            else:
                word, label = line.strip ().split ()
                par.append ((word, label))
        if par:
            bert_paragraphs.append (par)
    with open (xml_path, encoding = 'utf8') as fxml:
        text = fxml.read ()
        xml_paragraphs = find_paragraphs_with_words (text)
    assert len (bert_paragraphs) == len (xml_paragraphs)
    offset = 0
    annotated_text = ''
    for xpar, bpar in zip (xml_paragraphs, bert_paragraphs):
        for chunk_start, chunk_end in find_chunks (bpar):
            start = xpar[chunk_start][0]
            end = xpar[chunk_end][1]
            annotated_text += text[offset:start] + '<said>' + text[start:end] + '</said>'
            offset = end
    annotated_text += text[offset:]

    if save:
        if type (save) == str:
            output_path = save
        else:
            name, ext = os.path.splitext (xml_path)
            output_path = name + '_annotated' + ext
        with open (output_path, 'w', encoding = 'utf8') as fout:
            fout.write (annotated_text)
        print ('Annotated XML file saved: ', output_path)

    return annotated_text
