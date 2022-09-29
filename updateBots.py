import os
path = os.getcwd()
ls = os.listdir(path)
for file,db in ls:
    if file.endswith('.py') and not file.startswith('updateBots'):
        for line,code in enumerate(open(file, 'r'),1):
            if line == 1:
                newfile = str(code)
            elif 1 < line < 17:
                newfile = str(f'{newfile}{code}')
            else:
                break
for file in ls:
    if file is 'sb6.py':
        for line, code in enumerate(open(file, 'r'), 1):
            if line > 17:
                newfile = str(f'{newfile}{code}')
            else:
                print(newfile)
                open(file,'r').close()
                open(file,'w').write(newfile)
