import os

for fn in files:
	with open(fn, encoding='utf8') as fin:
		lines = fin.readlines()
	ind_p = 1
	ind_s = 1
	ind_ss = 1
	for i in range(len (lines)):
		if lines[i] == '<samples>\n':
			lines[i] = '<samples n="1">\n'
			continue
		if '<sample>' in lines[i]:
			lines[i] = re.sub('<sample>', r'<sample n="%d">' % ind_ss,
			lines[i])
			ind_ss += 1
			continue
		line = re.sub(r'<p>', r'<p n="%d">' % ind_p, lines[i])
		if line != lines[i]:
			ind_p += 1
		lines[i] = line
	with open(fn, 'w', encoding='utf8') as fout:
		fout.write(''.join(lines))
	os.remove(fn + '.new')
