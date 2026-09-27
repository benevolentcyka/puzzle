"""All independent LF-versus-CRLF choices in the format example."""


def variants(source):
    text=source.decode('ascii')
    if '\r' in text:
        return
    # Each of the 18 LF bytes can independently have a CR preceding it.
    pieces=text.split('\n')
    assert len(pieces)==19
    for mask in range(1 << 18):
        value=pieces[0]
        for i,piece in enumerate(pieces[1:]):
            value+= ('\r\n' if mask & (1<<i) else '\n') + piece
        yield value.encode(), {'mode':'independent-CR','mask':mask}
