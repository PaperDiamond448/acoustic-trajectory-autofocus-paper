"""Assemble the current manuscript using its existing figure-placement rules."""
from pathlib import Path
from urllib.parse import quote
import importlib.util
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'当前主线精选_20261003/11_正文稿/修订稿_20261005/_build'
def main():
    sys.path.insert(0,str(BUILD))
    spec=importlib.util.spec_from_file_location('paper_build',BUILD/'build_docx.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    md=module.assemble().read_text(encoding='utf-8')
    md=re.sub(r'(?<=\]\()img/([^\)]+)(?=\))',
              lambda m:quote((BUILD.relative_to(ROOT)/'img'/m.group(1)).as_posix(),safe='/'),md)
    md=re.sub(r'\)\{width=[^}]+\}',')',md)
    md=re.sub(r'^---\n.*?\n---\n','',md,count=1,flags=re.S)
    abstract=(module.MS/'摘要.md').read_text(encoding='utf-8').splitlines()
    title=abstract[0].lstrip('# ').strip()
    dst=ROOT/'在线阅读_完整修订稿.md'
    dst.write_text('# '+title+'\n\n'+md.strip()+'\n',encoding='utf-8')
    print('Updated',dst.relative_to(ROOT))
if __name__=='__main__':main()
