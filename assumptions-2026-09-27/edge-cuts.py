"""Exact byte prefixes/suffixes and bounded simultaneous cuts at both ends."""


def variants(source, width=256):
    for end in range(1,len(source)+1):
        yield source[:end], dict(edit='prefix',start=0,end=end)
    for start in range(1,len(source)):
        yield source[start:], dict(edit='suffix',start=start,end=len(source))
    for start in range(1,min(width,len(source)-2)+1):
        for removed in range(1,min(width,len(source)-start-1)+1):
            end = len(source)-removed
            yield source[start:end], dict(edit='both-edges',start=start,end=end)


def verify():
    count = 0
    for source in [b'a',b'ab',b'abcdefg',b'a\r\nb\xc2\xa0c']:
        for width in [0,1,2,256]:
            got = list(variants(source,width))
            intervals = {(label['start'],label['end']) for _,label in got}
            expected = {(a,b) for a in range(len(source)) for b in range(a+1,len(source)+1)
                        if a==0 or b==len(source) or (a<=width and len(source)-b<=width)}
            assert intervals==expected and len(got)==len(expected)
            for text,label in got:
                assert text==source[label['start']:label['end']]
                count+=1
    return count
