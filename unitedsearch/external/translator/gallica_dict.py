"""
Dictionary for Gallica translation
"""
dictionary={
    'keywords':'all',
    'creator':'artist',
    'title':'title',
    'start date':'start date',
    'end date':'end date',
    'year':'start date',
    'publisher':'publisher',
    'decade':'start date',
    'century':'start date',
    'rights': 'copyright',
    'isbn':'isbn',
    'source':'source',
    'table':'table',
    'subject':'subject',
    'language':'languages',
    '-':'except',
    '?':'or',
    '': 'all'
}


query_dict={
    'f_allcontent' :'',
    'f_creator':'creator',
    'f_artist':'creator',
    'f_title':'title',
    'start date':'start date',
    'end date':'end date',
    'publisher':'publisher',
    'copyright':'rights',
    'f_allmetadata':'isbn',
    'source':'source',
    'table':'table',
    'subject':'subject',
    'languages':'language',
    'MUST_NOT':'-',
    'SHOULD':'?',
    'MUST':''
}