#!/usr/bin/python3
# Copyright (c) 2003-2020  Pavel Rychly, Vojtech Kovar, Milos Jakubicek,
#                          Milos Husak, Vit Baisa

import manatee
import os, re, sys
from butils import set_proctitle
from conccache import add_to_map, del_from_map, load_map, get_cached_conc,\
                      get_existing_conc, get_existing_conc_sizes
from pyconc import PyConc

def tokens2strclass (tokens):
    return [{'str': tokens[i], 'class': tokens[i+1].strip ('{}')}
            for i in range(0, len(tokens), 2)]


def printkwic (conc, froml=0, tol=5, leftctx='15#', rightctx='15#',
               attrs='word', refs='#', maxcontext=0):
    def strip_tags (tokens):
        return ''.join ([tokens[i] for i in range(0, len(tokens), 2)])
    kl = manatee.KWICLines (conc.corp(), conc.RS (True), leftctx, rightctx,
                            attrs, 'word', 'p', refs, maxcontext)
    while kl.nextline ():
        print('%s %s <%s> %s' % (kl.get_refs(), strip_tags (kl.get_left()),
                                 strip_tags (kl.get_kwic()),
                                 strip_tags (kl.get_right())))


def pos_ctxs (min_hitlen, max_hitlen, max_ctx=3):
    ctxs = [{'n': '%iL' % -c, 'ctx':'%i<0' % c} for c in range (-max_ctx, 0)]
    if max_hitlen == 1:
        ctxs.append ({'n': 'Node', 'ctx': '0~0>0'})
    else:
        ctxs.extend ([{'n':'Node %i' % c, 'ctx':'%i<0' % c}
                      for c in range (1,max_hitlen+1)])
    ctxs.extend ([{'n': '%iR' % c, 'ctx':'%i>0' % c}
                  for c in range (1, max_ctx+1)])
    return ctxs


def kwicpage (conc, fromp=1, leftctx='40#', rightctx='40#', attrs='word',
              ctxattrs='word', refs='#', structs='p', pagesize=20,
              labelmap={}, righttoleft=False, alignlist=[],
              tbl_template='none', hidenone=0, viewmode='kwic', reflinks=[]):
    try:
        fromp = int(fromp)
        if fromp < 1:
            fromp = 1
    except:
        fromp = 1
    corps_with_colls = manatee.StrVector()
    conc.get_aligned(corps_with_colls)
    if not conc.orig_corp.get_conffile() in corps_with_colls:
        kwcl = kwiclines (conc, (fromp -1) * pagesize, fromp * pagesize,
                          '0', '0', 'word', '', refs, structs,
                          labelmap, righttoleft, viewmode, reflinks)
    else:
        kwcl = kwiclines (conc, (fromp -1) * pagesize, fromp * pagesize,
                          leftctx, rightctx, attrs, ctxattrs, refs, structs,
                          labelmap, righttoleft, viewmode, reflinks)
    out = {'Lines': kwcl}
    add_aligns(out, conc,(fromp -1) * pagesize, fromp * pagesize,
               leftctx, rightctx, attrs, ctxattrs, refs, structs,
               labelmap, righttoleft, alignlist)
    if tbl_template != 'none':
        try:
            from tbl_settings import tbl_refs, tbl_structs
            sen_refs = tbl_refs.get(tbl_template, '') + ',#'
            sen_structs = tbl_structs.get(tbl_template, '') or 'g'
        except ImportError:
            sen_refs = ',#'
            sen_structs = 'g'
        sen_lines = kwiclines(conc, (fromp -1) * pagesize, fromp * pagesize,
                             '-1:s', '1:s', refs=sen_refs, structs=sen_structs,
                             viewmode=viewmode)
        for old, new in zip(out['Lines'], sen_lines):
            old['Sen_Left'] = new['Left']
            old['Sen_Right'] = new['Right']
            old['Sen_Kwic'] = new['Kwic']
            old['Tbl_refs'] = new['Refs']
    if conc.size() > pagesize:
        out['fromp'] = fromp
    out['concsize'] = conc.size()
    if hidenone:
        for line in out['Lines']:
            for part in ('Kwic', 'Left', 'Right'):
                for item in line[part]:
                    item['str'] = item['str'].replace('===NONE===', '')
    return out

def add_aligns(result, conc, fromline, toline, leftctx='40#', rightctx='40#',
               attrs='word', ctxattrs='word', refs='#', structs='p',
               labelmap={}, righttoleft=False, alignlist=[]):
    if not alignlist: return
    al_lctx = leftctx.endswith('#') and '0' or leftctx
    al_rctx = rightctx.endswith('#') and '0' or rightctx
    al_lines = []
    corps_with_colls = manatee.StrVector()
    conc.get_aligned(corps_with_colls)
    for al_corp in alignlist:
        al_corpname = al_corp.get_conffile()
        if al_corpname in corps_with_colls:
            conc.switch_aligned (al_corp.get_conffile())
            al_lines.append (kwiclines (conc, fromline, toline, leftctx,
                                        rightctx, attrs, ctxattrs, refs,
                                        structs, labelmap,
                                        al_corp.get_conf('RIGHTTOLEFT') == '1'))
        else:
            conc.switch_aligned(conc.orig_corp.get_conffile())
            conc.add_aligned(al_corp.get_conffile())
            conc.switch_aligned (al_corp.get_conffile())
            al_lines.append (kwiclines (conc, fromline, toline, al_lctx,
                                        al_rctx, attrs, '', refs, structs,
                                        labelmap,
                                        al_corp.get_conf('RIGHTTOLEFT') == '1'))
            for al_line in al_lines[-1]:
                al_line['has_no_kwic'] = True
    aligns = list(zip(*al_lines))
    for i, line in enumerate(result['Lines']):
        line['Align'] = aligns[i]

def kwiclines (conc, fromline, toline, leftctx='40#', rightctx='40#',
               attrs='word', ctxattrs='word', refs='#', structs='p',
               labelmap={}, righttoleft=False, viewmode='kwic', reflinks=[]):
    lines = []
    # TODO: should be probably refs and refs.count(',') + 1 or 0
    refslen = refs.count(',') + 1
    if len(reflinks):
        refs = refs + ',=' + ',='.join(reflinks)
    leftlabel, rightlabel = 'Left', 'Right'
    if righttoleft:
        if viewmode == 'kwic':
            rightlabel, leftlabel = 'Left', 'Right'
        structs += ',ltr'
        #from unicodedata import bidirectional
        def isengword (strclass):
            #return bidirectional(word[0]) in ('L', 'LRE', 'LRO')
            return 'ltr' in strclass['class'].split()

    kl = manatee.KWICLines (conc.corp(), conc.RS (True, fromline, toline),
                            leftctx, rightctx, attrs, ctxattrs, structs, refs)
    labelmap = labelmap.copy()
    labelmap[0] = '_'
    while kl.nextline():
        linegroup = kl.get_linegroup() or 0
        linegroup = labelmap.get(linegroup, '_')
        leftwords = tokens2strclass (kl.get_left())
        rightwords = tokens2strclass (kl.get_right())
        kwicwords = tokens2strclass (kl.get_kwic())
        if righttoleft and kwicwords:
            # change order for "English" context of "English" keywords
            if isengword(kwicwords[0]):
                # preceding words
                nprev = len(leftwords) -1
                while nprev >= 0 and isengword (leftwords[nprev]):
                    nprev -= 1
                if nprev == -1:
                    # move whole context
                    moveleft = leftwords
                    leftwords = []
                else:
                    moveleft = leftwords[nprev+1:]
                    del leftwords[nprev+1:]

                # following words
                nfollow = 0
                while (nfollow < len(rightwords)
                       and isengword (rightwords[nfollow])):
                    nfollow += 1
                moveright = rightwords[:nfollow]
                del rightwords[:nfollow]

                leftwords = leftwords + moveright
                rightwords = moveleft + rightwords

        reflist = list(kl.get_ref_list())
        links = []
        for i, ref in enumerate(reflist[refslen:]):
            if ref in ('', '===NONE==='):
                continue
            link_tmpl = conc.corp().get_conf(reflinks[i] + '.URLTEMPLATE')
            mtype = conc.corp().get_conf(reflinks[i] + '.MEDIATYPE')
            info = conc.corp().get_conf(reflinks[i] + '.INFO')
            struct_attr = reflinks[i]
            links.append({'url': link_tmpl % ref,
                          'mediatype': mtype,
                          'struct_attr': struct_attr,
                          'info': info or None
                          })
        lines.append ({'toknum': kl.get_pos(),
                       'hitlen': kl.get_kwiclen(),
                       'Refs': reflist[:refslen],
                       'Tbl_refs': reflist[:refslen],
                       leftlabel: leftwords,
                       'Kwic': kwicwords,
                       rightlabel: rightwords,
                       'Links': links,
                       'linegroup': linegroup,
                       'linegroup_id': kl.get_linegroup() or 0
                       })
    return lines


def strkwiclines (conc, fromline, toline=None, leftctx='40#', rightctx='40#'):
    def tokens2str (tokens):
        return ''.join ([tokens[i] for i in range(0, len(tokens), 2)])
    toline = toline or fromline +1
    kl = manatee.KWICLines (conc.corp(), conc.RS (True, fromline, toline),
                            leftctx, rightctx, 'word', 'word','','')
    return [{'left': tokens2str (kl.get_left()),
             'kwic': tokens2str (kl.get_kwic()),
             'right': tokens2str (kl.get_right())}
            for line in range (fromline, toline) if kl.nextline ()]


def get_sort_idx (conc, q=[], pagesize=20, enc='latin1'):
    crit = ''
    for qq in q:
        if qq.startswith('s') and not qq.startswith('s*'): crit = qq[1:]
    if not crit: return []
    vals = manatee.StrVector(); idx = manatee.IntVector()
    if '.' in crit.split('/')[0]: just_letters = False
    else: just_letters = True
    conc.sort_idx(crit, vals, idx, just_letters)
    out = list(zip(vals, idx))
    if just_letters:
        result = []; keys = []
        for v, p in out:
            if not v[0] in keys:
                result.append((v[0], p)); keys.append(v[0])
        out = result
    return [{'pos': p, 'label': v} for v, p in out]

def get_conc_sizes (corp, q=[], _cache_dir="cache", server_port=None):
    return get_existing_conc_sizes (corp, q, _cache_dir, server_port)

def compute_conc (corp, q, _cache_dir, subchash, samplesize, fullsize, pid_dir,
                  save):
    q = tuple (q)
    if q[0][0] == "R": # online sample
        if fullsize == -1: # need to compute original conc first
            q_copy = list(q)
            q_copy[0] = q[0][1:]
            q_copy = tuple(q_copy)
            conc = get_sync_conc (corp, q_copy, save, _cache_dir, pid_dir,
                                  subchash, samplesize, fullsize)
            fullsize = conc.fullsize()
        return PyConc (corp, q[0][1], q[0][2:], samplesize, fullsize)
    else:
        return PyConc (corp, q[0][0], q[0][1:], samplesize)

def get_sync_conc (corp, q, save, _cache_dir, pid_dir, subchash, samplesize,
                   fullsize):
    conc = None
    if save: # save=0 => processes entirely independent
        cachefile, pidfile, server = add_to_map (_cache_dir, pid_dir,
                                                 subchash, q[:1], -1)
        if type(server) == int: # computation got started meanwhile
            conc = get_existing_conc (corp, subchash, q[:1], _cache_dir,
                                      pid_dir, -1, server)
    if not conc:
        try:
            conc = compute_conc (corp, q, _cache_dir, subchash, samplesize,
                                 fullsize, pid_dir, save)
            if save:
                server.timeout = 1
                server.conc = conc
                while True:
                    server.handle_request()
                    if conc.finished():
                        conc.save (cachefile)
                        add_to_map (_cache_dir, pid_dir, subchash, q[:1],
                                    conc.size()) # update size in map file
                        os.remove (pidfile.encode("utf-8"))
                        break
            else:
                conc.sync()
        except:
            del_from_map (_cache_dir, subchash, q[:1])
            raise
    return conc

def get_async_conc (corp, q, save, _cache_dir, pid_dir, subchash, samplesize,
                    fullsize, minsize):
    r, w = os.pipe()
    r, w = os.fdopen(r,'rb'), os.fdopen(w,'wb')
    if os.fork() == 0: # child
        r.close() # child writes
        title = "conc;%s;%s;%s;" % (corp.get_conffile(), q[0][0], q[0][1:])
        set_proctitle(title)
        # close stdin/stdout/stderr so that the webserver closes
        # connection to client when parent ends, comment for debugging
        os.close(0); os.close(1); os.close(2)
        try:
            cachefile, pidfile, server = add_to_map(_cache_dir, pid_dir,
                                                    subchash, q, -1)
            if type(server) == int:
                # conc got started meanwhile by another process
                w.write (str(server).encode())
                w.close()
                os._exit(0)
            sys.stderr = server.logfile
            conc = compute_conc (corp, q, _cache_dir, subchash,
                                 samplesize, fullsize, pid_dir, save)
            w.write (str(server.server_port).encode())
            w.close()
            server.timeout = 5
            server.conc = conc
            while True:
                server.handle_request()
                if conc.finished():
                    conc.save (cachefile)
                    break
            # update size in map file
            add_to_map (_cache_dir, pid_dir, subchash, q, conc.size())
            os.remove (pidfile)
            os._exit(0)
        except Exception as e:
            import traceback, pickle
            if not w.closed:
                stack = traceback.format_exception(*sys.exc_info())
                e = (e, stack)
                w.write (pickle.dumps(e))
                w.close()
            traceback.print_exc (None, open(pidfile, "a"))
            del_from_map (_cache_dir, subchash, q)
            os._exit(0)
    else: # parent
        w.close() # parent reads
        server_port = r.read()
        try:
            server_port = int (server_port.decode())
        except ValueError as msg:
            if not server_port:
                raise ValueError('Error while computing concordance')
            else:
                import pickle
                e = pickle.loads (server_port)
                args = ' '.join(e[0].args)
                if len(args) < 3:
                    args = args + '\n' + ''.join(e[1])
                raise Exception(args)
        r.close()
        conc = get_existing_conc (corp, subchash, q, _cache_dir, pid_dir,
                                  minsize, server_port)
        conc.port = server_port
        return conc

def get_conc (corp, minsize=None, q=[], fromp=0, pagesize=0, asyn=0, save=0, \
              _cache_dir='cache', samplesize=0, debug=False):
    if not q:
        return None
    q = tuple (q)
    if not minsize:
        if len(q) > 1 or not asyn: # subsequent concordance processing
                                    # by its methods needs whole concordance
            minsize = -1
        else:
            minsize = fromp * pagesize
    _cache_dir = _cache_dir + '/' + corp.corpname + '/'
    pid_dir = _cache_dir + "/run/"
    subchash = getattr(corp, 'subchash', None)
    conc = None
    fullsize = -1

    # try to locate concordance in cache
    if save:
        toprocess, conc = get_cached_conc(corp, subchash, q, _cache_dir,
                                          pid_dir, minsize)
        if toprocess == len(q):
            save = 0
        if not conc and q[0][0] == "R": # online sample
            q_copy = list(q)
            q_copy[0] = q[0][1:]
            t, c = get_cached_conc (corp, subchash, q_copy, _cache_dir,
                                    pid_dir, -1)
            if c:
                fullsize = c.fullsize()
    else:
        asyn = 0

    # cache miss or not used
    if not conc:
        toprocess = 1
        if asyn and len(q) == 1: # asynchronous processing
            conc = get_async_conc (corp, q, save, _cache_dir, pid_dir,
                                   subchash, samplesize, fullsize, minsize)
        else: # synchronous processing
            conc = get_sync_conc (corp, q, save, _cache_dir, pid_dir,
                                  subchash, samplesize, fullsize)

    # process subsequent concordance actions
    for act in range(toprocess, len(q)):
        command = q[act][0]
        getattr (conc, 'command_' + command) (q[act][1:]) # call command_*(query) from pyconc
        if command in 'gaLE':# user specific/volatile actions, cannot save
            save = 0
        if save:
            cachefile, pidfile, server = add_to_map (_cache_dir, pid_dir,
                                                     subchash, q[:act + 1],
                                                     conc.size())
            if type(server) != int: # nobody started the computation yet
                conc.save (cachefile)
                os.remove (pidfile)
    return conc


def get_conc_desc (q=[], _cache_dir='cache', corpname='', subchash=None):
    desctext = {'q': 'Query',
                'a': 'Query',
                'L': 'Label filter',
                'R': 'Query',
                'r': 'Random sample',
                's': 'Sort',
                'f': 'Shuffle',
                'D': 'Subparts filter',
                'F': 'Filter all but first hit in the structure',
                'n': 'Negative filter',
                'N': 'Negative filter (excluding KWIC)',
                'p': 'Positive filter',
                'P': 'Positive filter (excluding KWIC)',
                'w': 'Word sketch item',
                't': 'Term',
                'e': 'GDEX',
                'x': 'Switch KWIC',
                'X': 'Filter by aligned corpus',
                'g': 'Sort labels',
                }
    forms = {'q': ('first_form', 'cql'),
             'a': ('first_form', 'cql'),
             'r': ('reduce_form', 'rlines'),
             }
    desc = []
    saved = load_map (_cache_dir + '/' + corpname + '/')
    q = tuple (q)

    for i in range (len(q)):
        size = saved.get ((subchash, q[:i+1]), ('',''))[1]
        # TODO: L operation is missing size
        opid = q[i][0]
        if opid == 'L':
            args = str(abs(int(q[i].split()[-1])))
        else:
            args = q[i][1:]
        url1p = [('q', qi) for qi in q[:i]]
        url2p = [('q', qi) for qi in q[:i+1]]
        op = desctext.get (opid)
        formname = forms.get(opid, ('',''))
        da = ''
        if formname[1]:
            if formname[1] == 'cql':
                if opid == 'a':
                    default_attr, url1args = args.split(',', 1)
                    args = url1args
                else: default_attr, url1args = 'word', args
                url1p.append (('queryselector', 'cqlrow'))
                url1p.append (('default_attr', default_attr))
                da = default_attr
            else:
                url1args = args
            url1p.append ((formname[1], url1args))
        if opid == 's' and args[0] != '*' and i > 0 and len (args.split()) > 2:
            op = 'Multilevel Sort'
        if op:
            if not formname[0]: url1p = ''
            desc.append ((op, args, url1p, url2p, size, formname[0], da))
    return desc

def get_full_ref (corp, pos):
    data = {}
    fullref = corp.get_conf('FULLREF').split(',')
    ds = corp.get_conf('DOCSTRUCTURE')
    refs = [(n, str(pos) if n == '#' else corp.get_attr(n).pos2str(pos))
            for n in fullref]
    data['Refs'] = [{'name': n == '#' and 'Token number'
                             or corp.get_conf (n+'.LABEL') or n,
                     'id': n,
                     'val': v}
                    for n,v in refs]
    if ds + '#' not in fullref:
        data['Refs'].insert(0, {
            'name': 'Document number',
            'id': ds + '#',
            'val': str(corp.get_struct(ds).num_at_pos(pos))})
    if '#' not in fullref:
        data['Refs'].insert(0, {
            'name': 'Token number',
            'id': '#',
            'val': str(pos)})
    for n, v in refs:
        data[n.replace('.','_')] = v
    return data


def get_detail_context (corp, pos, hitlen=1,
                        detail_left_ctx=40, detail_right_ctx=40,
                        addattrs=[], structs='', detail_ctx_incr=60):
    data = {}
    wrapdetail = corp.get_conf ('WRAPDETAIL')
    if wrapdetail:
        data['wrapdetail'] = '<%s>' % wrapdetail
        if not wrapdetail in structs.split(','): data['deletewrap'] = True
        structs = wrapdetail + ',' + structs
    else:
        data['wrapdetail'] = ''
    try:
        maxdetail = int (corp.get_conf ('MAXDETAIL'))
    except:
        maxdetail = 0
    if corp.corpname.startswith('user/'):
        maxdetail = 0
    if maxdetail:
        if detail_left_ctx > maxdetail:
            detail_left_ctx = maxdetail
        if detail_right_ctx > maxdetail:
            detail_right_ctx = maxdetail
    if detail_left_ctx > pos:
        detail_left_ctx = pos
    attrs = ','.join(['word'] + addattrs)
    cr = manatee.CorpRegion(corp, attrs, structs)
    region_left = tokens2strclass (cr.region (pos - detail_left_ctx, pos))
    region_kwic = tokens2strclass (cr.region (pos, pos + hitlen))
    region_right = tokens2strclass (cr.region(pos + hitlen,
                                              pos + hitlen + detail_right_ctx))
    for seg in region_left + region_kwic + region_right:
        seg['str'] = seg['str'].replace('===NONE===', '')
        if 'conc' in seg['class']:
            c = [x for x in seg['class'].split() if x.startswith('conc')][0]
            seg['color'] = c[4:]
            seg['class'] = seg['class'].replace(c, '').strip()
        elif '#' in seg['class']:
            c = [x for x in seg['class'].split() if x.startswith('#')][0]
            seg['color'] = c
            seg['class'] = seg['class'].replace(c, '').strip()
    for seg in region_kwic:
        if not seg['class']: seg['class'] = 'coll'
    data['content'] = region_left + region_kwic + region_right
    refbase = 'pos=%i;' % pos
    if hitlen != 1: refbase += 'hitlen=%i;' % hitlen
    data['leftlink'] = refbase + ('detail_left_ctx=%i;detail_right_ctx=%i'
                                  % (detail_left_ctx + detail_ctx_incr,
                                     detail_right_ctx))
    data['rightlink'] = refbase + ('detail_left_ctx=%i;detail_right_ctx=%i'
                                   % (detail_left_ctx,
                                      detail_right_ctx + detail_ctx_incr))
    if corp.get_conf('RIGHTTOLEFT') == '1': data['righttoleft'] = True
    data['pos'] = pos
    data['maxcontext'] = maxdetail
    return data


def fcs_search(corp, fcs_query, max_rec, start):
    "aux function for federated content search: operation=searchRetrieve"
    if not fcs_query:
        raise Exception(7, 'fcs_query', 'Mandatory parameter not supplied')
    query = fcs_query.replace('+', ' ') # convert URL spaces
    exact_match = False # attr=".*value.*"
    if 'exact' in query.lower() and not '=' in query: # lemma EXACT "dog"
        pos = query.lower().index('exact') # first occurence of EXACT
        query = query[:pos] + '=' + query[pos+5:] # 1st exact > =
        exact_match = True
    rq = '' # query for manatee
    try: # parse query
        if '=' in query: # lemma=word | lemma="word" | lemma="w1 w2" | word=""
            attr, term = query.split('=')
            attr = attr.strip()
            term = term.strip()
        else: # "w1 w2" | "word" | word
            if 'lemma' in corp.get_conf('ATTRLIST').split(','):
                attr = 'lemma'
            else:
                attr = 'word'
            term = query.strip()
        if '"' in attr:
            raise Exception
        if '"' in term: # "word" | "word1 word2" | "" | "it is \"good\""
            if term[0] != '"' or term[-1] != '"': # check q. marks
                raise Exception
            term = term[1:-1].strip() # remove quotation marks
            if ' ' in term: # multi-word term
                if exact_match:
                    rq = ' '.join(['[%s="%s"]' % (attr, t)
                            for t in term.split()])
                else:
                    rq = ' '.join(['[%s=".*%s.*"]' % (attr, t)
                            for t in term.split()])
            elif term.strip() == '': # ""
                raise Exception # empty term
            else: # one-word term
                if exact_match:
                    rq = '[%s="%s"]' % (attr, term)
                else:
                    rq = '[%s=".*%s.*"]' % (attr, term)
        else: # must be single-word term
            if ' ' in term:
                raise Exception
            if exact_match: # build query
                rq = '[%s="%s"]' % (attr, term)
            else:
                rq = '[%s=".*%s.*"]' % (attr, term)
    except: # there was a problem when parsing
        raise Exception(10, query, 'Query syntax error')
    if not attr in corp.get_conf('ATTRLIST'):
        raise Exception(16, attr, 'Unsupported index')
    try: # try to get concordance
        conc = get_conc(corp, q=['q' + rq])
    except Exception as e:
        raise Exception(10, repr(e), 'Query syntax error')
    page = kwicpage(conc) # convert concordance
    if len(page['Lines']) < start:
        raise Exception(61, 'startRecord', 'First record position out of range')

    return [(kwicline['Left'][0]['str'], kwicline['Kwic'][0]['str'],
            kwicline['Right'][0]['str'], kwicline['Refs'])
            for kwicline in page['Lines']][start:][:max_rec]


def fcs_scan(corpname, scan_query, max_ter, start):
    "aux function for federated content search: operation=scan"
    if not scan_query:
        raise Exception(7, 'scan_query', 'Mandatory parameter not supplied')
    query = scan_query.replace('+', ' ') # convert URL spaces
    exact_match = False
    if 'exact' in query.lower() and not '=' in query: # lemma ExacT "dog"
        pos = query.lower().index('exact') # first occurence of EXACT
        query = query[:pos] + '=' + query[pos+5:] # 1st exact > =
        exact_match = True
    corp = manatee.Corpus(corpname)
    attrs = corp.get_conf('ATTRLIST').split(',') # list of available attrs
    try:
        if '=' in query:
            attr, value = query.split('=')
            attr = attr.strip()
            value = value.strip()
        else: # must be in format attr = value
            raise Exception
        if '"' in attr:
            raise Exception
        if '"' in value:
            if value[0] == '"' and value[-1] == '"':
                value = value[1:-1].strip()
            else:
                raise Exception
    except Exception as e:
        raise Exception(10, scan_query, 'Query syntax error')
    if not attr in attrs:
         raise Exception(16, attr, 'Unsupported index')
    import corplib
    if exact_match:
        wlpattern = '^' + value + '$'
    else:
        wlpattern = '.*' + value + '.*'

    wl = corp.get_attr(attr)
    sortfreq = wl.get_stat('frq')
    addfreqs = []
    nwre = None
    wlwords = []
    blacklist = []
    wlminfreq = 5
    wlmaxfreq = 0
    wlmaxitems = 100

    result_list, _, _ = corplib.manatee.wordlist (wl, wlpattern, addfreqs,
                              sortfreq, wlwords, blacklist, wlminfreq,
                              wlmaxfreq, wlmaxitems, nwre)
    return [d.split('\v') for d in result_list][start:][:max_ter]

def translate_words(c1, c2, data):
    "translate words"
    from translate import Translator
    c2 = manatee.Corpus(c2)
    dictname = '%s-%s' % (c1.get_conf('LANGUAGE'), c2.get_conf('LANGUAGE'))
    translator = Translator(dictname)
    if not translator:
        return {'error': "Unsupported language pair %s" % (dictname)}
    return {'data': translator.get_subdict(data.split(','))}

def translate_kwic(c1, corpname2, data):
    "translates tokens (tokenums) into lemmata in corpus2 using pcdicts"
    from translate import Translator
    c2 = manatee.Corpus(corpname2)
    try:
        alignstruct = c1.get_conf('ALIGNSTRUCT')
        align = c1.get_struct(alignstruct)
    except Exception as e:
        return ({}, {})
    dictname = '%s-%s' % (c1.get_conf('LANGUAGE'), c2.get_conf('LANGUAGE'))
    translator = Translator(dictname)
    if not translator:
        return ({}, {})
    translations = {}
    toknum2words = {}
    try:
        attr = c1.get_attr('lemma')
    except:
        attr = c1.get_attr('word')
    MAXHITLEN = 3 # do not translate very long KWICs
    for item in data.split('\t'):
        toknum, hitlen = item.split(':')
        for i in range(min(MAXHITLEN, int(hitlen))):
            p = int(toknum)+i
            ltt = attr.id2str(attr.pos2id(p))#.lower()
            toknum2words[p] = ltt
            if ltt not in list(translations.keys()):
                translations[ltt] = set([(s, w.lower())
                        for s,w in translator.get_translations(ltt)])
            if align:
                align_n = align.num_at_pos(p)
                conc = manatee.Concordance(c1, '<%s #%d>' %\
                        (alignstruct, align_n), 0, -1)
                conc.sync()
                conc.add_aligned(c2.get_conffile())
                conc.switch_aligned(c2.get_conffile())
                for l, w in zip(
                        kwiclines(conc, 0, 1, '-1:s', '1:s', attrs='lemma'),
                        kwiclines(conc, 0, 1, '-1:s', '1:s', attrs='word')):
                    for ctx in ['Left', 'Kwic', 'Right']:
                        if l[ctx] and w[ctx] and l[ctx][0]['str'] \
                                and w[ctx][0]['str']:
                            for t1, t2 in zip(l[ctx][0]['str'].split(),
                                    w[ctx][0]['str'].split()):
                                if t1.lower() in translations[ltt]:
                                    translations[ltt].add((
                                            translations[ltt][t1.lower()][0],
                                            t2.lower()))#x0.9?
    for k in translations:
        translations[k] = [x[1] for x in sorted(list(translations[k]), reverse=True)]
    return (translations, toknum2words)
