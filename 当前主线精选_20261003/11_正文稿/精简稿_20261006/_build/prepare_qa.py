from pathlib import Path
OLD=Path(__file__).resolve().parent.parent.parent/'修订稿_20261005'/'_build'/'源文件同步_20261006'
WORK=Path(__file__).resolve().parent/'排版核查'
WORK.mkdir(exist_ok=True)
export=(OLD/'export_variants.py').read_text(encoding='utf-8').replace('论文修订稿_中文_20261006','论文精简稿_中文_20261006')
(WORK/'export_variants.py').write_text(export,encoding='utf-8')
render=(OLD/'render_variants.py').read_text(encoding='utf-8')
render=render.replace("print('Rendered 51 manuscript pages and 52 review pages.')", "print('Rendered pages:', {k:len(v) for k,v in pdfs.items()})")
render=render.replace("'/ 51'", "'/',len(main)")
render=render.replace("main=pdfs['正文版']", "main=pdfs['正文版']\nassert len(pdfs['审阅目录版']) == len(main)+1, 'Check page pairing before visual QA'")
(WORK/'render_variants.py').write_text(render,encoding='utf-8')
print('Prepared export then render workflow')
