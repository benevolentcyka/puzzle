"""Explicit editor/clipboard transformations, not arbitrary case radii."""
import hashlib
import html
import itertools
import json
import re
import urllib.parse


def typography(text):
    # Coherent replacements across the buffer, not one-letter neighborhoods.
    for quote_mode, apostrophe, ellipsis in itertools.product(
            ['straight','curly','left','right','guillemets'], ["'",'\u2019','\u2018'], [False,True]):
        value = text
        if quote_mode == 'curly':
            value = re.sub(r'"([^"\r\n]*)"', lambda m:'\u201c'+m[1]+'\u201d', value)
        elif quote_mode == 'left':
            value = value.replace('"','\u201c')
        elif quote_mode == 'right':
            value = value.replace('"','\u201d')
        elif quote_mode == 'guillemets':
            value = re.sub(r'"([^"\r\n]*)"', lambda m:'\u00ab'+m[1]+'\u00bb', value)
        value = value.replace("'",apostrophe)
        if ellipsis:
            value = value.replace('...','\u2026')
        yield value, {'quotes':quote_mode,'apostrophe':apostrophe,'ellipsis':ellipsis}


def variants(source):
    text = source.decode('utf8')
    for value, label in typography(text):
        for encoding in ['utf8','utf-16-le','utf-16-be']:
            yield value.encode(encoding), dict(label,encoding=encoding)
    forms = {
        'html-text': html.escape(text,quote=False),
        'html-quotes': html.escape(text,quote=True),
        'literal-lf': text.replace('\r','\\r').replace('\n','\\n'),
        'json-string': json.dumps(text,ensure_ascii=True),
        'json-interior': json.dumps(text,ensure_ascii=True)[1:-1],
        'url': urllib.parse.quote(text,safe=''),
        'form': urllib.parse.quote_plus(text,safe=''),
        'all-lower': text.lower(),
        'all-upper': text.upper(),
        'all-swapped': text.swapcase(),
        'title-words': text.title(),
    }
    for name,value in forms.items():
        yield value.encode(), {'format':name}
    # Paragraphs copied into or out of a simple HTML editor.
    paras=re.split(r'\r?\n\r?\n',text)
    for tag,escape,separator in itertools.product(['p','div'],[False,True],['','\n','\r\n']):
        value=separator.join(f'<{tag}>'+ (html.escape(p,quote=True) if escape else p) + f'</{tag}>' for p in paras)
        yield value.encode(), {'format':'html-paragraphs','tag':tag,'escaped':escape,'separator':separator}
    # A manual global replacement of the explicitly named quoted words/letters.
    for mapping in [{'I':'i'},{'n':'N'},{'himself':'himselF'},{'capitalization':'capitalizatioN'},
                    {'I':'i','n':'N'},{'I':'i','himself':'himselF'},
                    {'I':'i','n':'N','himself':'himselF','capitalization':'capitalizatioN'}]:
        for scope in ['word','substring','quoted']:
            value=text
            for before,after in mapping.items():
                if scope=='word':
                    value=re.sub(r'\b'+re.escape(before)+r'\b',after,value)
                elif scope=='quoted':
                    value=value.replace('"'+before+'"','"'+after+'"')
                else:
                    value=value.replace(before,after)
            yield value.encode(), {'format':'global-replace','mapping':mapping,'scope':scope}
