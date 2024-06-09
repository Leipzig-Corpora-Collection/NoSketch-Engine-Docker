# Copyright (c) 2003-2020  Pavel Rychly, Vojtech Kovar, Milos Jakubicek, Milos Husak, Vit Baisa

from CGIPublisher import correct_types
from usercgi import UserCGI
import corplib, conclib
from corplib import corpconf_pairs
import os
import sys
import gdex
import manatee
from pyconc import PyConc
from manatee import regexp_pattern
import time
import glob
from collections import defaultdict
from butils import *
from annotlib import Annotation
from conclib import strkwiclines


def onelevelcrit (prefix, attr, ctx, pos, fcode, icase, bward='', empty=''):
    fromcode = {'lc': '<0', 'rc': '>0', 'kl': '<0', 'kr': '>0'}
    if type(icase) == type(True):
        icase = {True: 'i', False: ''}[icase]
    if type(bward) == type(True):
        bward = {True: 'r', False: ''}[bward]
    suffix = '%s%s%s' % (icase, bward, empty)
    attrpart = '%s%s%s%s ' % (prefix, attr, '/' if suffix != '' else '', suffix)
    if not ctx:
        ctx = '%i%s' % (pos, fromcode.get (fcode, '0'))
    if '~' in ctx and '.' in attr:
        ctx = ctx.split('~')[0]
    return attrpart + ctx

def multilevel_sort_crit(mlsort_options):
    "multilevel sort for Platypus"
    prefix = 's'
    result = ''
    for opt in mlsort_options:
        if opt['ctx'] == '0': ctx = '0<0~0>0' # 0 == KWIC
        elif int(opt['ctx']) > 0: ctx = opt['ctx'] + '>0' # 0 == KWIC
        else: ctx = opt['ctx']
        result += onelevelcrit(prefix, opt['attr'], ctx, '', '',
                               opt.get('icase', ''), opt.get('bward', ''))
        prefix = ' '
    return result

def nicearg(arg):
    args = arg.split('"');
    niceargs = []
    niceargsset = set()
    for i in range(len(args)):
        if (i % 2):
            tmparg = args[i].strip('\\').replace('(?i)', '')
            if tmparg not in niceargsset:
                niceargs.append(tmparg)
                niceargsset.add(tmparg)
        else:
            if args[i].startswith('within'):
                niceargs.append('within')
    return ', '.join(niceargs)

def group_freqs_result(items):
    items.sort(key=lambda x: x['Word'][0]['n'])
    i = 1
    prev_w = items[0]['Word'][0]['n']
    items[0]['Subitems'] = []
    while i < len(items):
        w = items[i]['Word'][0]['n']
        if w == prev_w:
            items[i-1]['Subitems'].append(items[i])
            del items[i]
        else:
            prev_w = w
            items[i]['Subitems'] = []
            i += 1
    items.sort(key=lambda x: -x['frq'])
    newitems = []
    for item in items:
        newitems.append(item)
        for subitem in item['Subitems']:
            newitems.append(subitem)
        del item['Subitems']
    return newitems

def bgjob_info(out):
    return { 'processing': out["progress"] == '100' and '99' or out["progress"],
             'bgjob_notification': out['notifyme'] and 'checked' or '',
             'jobid': out["jobid"], 'esttime': out["esttime"],
             'desc': out["desc"]}


def sentence(s):
    def specific(s):
        # fix bracket placeholders in old corpus (tltenten18)
        for pat, repl in [(r'-lrb-', r'('), (r'-rrb-', r')'),
                          (r'-lsb-', r'['), (r'-rsb-', r']'),
                          (r'-lcb-', r'{'), (r'-rcb-', r'}')]:
            s = re.sub(pat, repl, s)
        return s

    def whitespace(s):
        s = re.sub(r'\s+', r' ', s) # replace (possibly multiple) whitespace with a single space
        s = s.strip() # strip whitespace from begin and end
        s = re.sub(r'\s+([.,!?:;])', r'\1', s) # remove whitespace before punctuation
        return s

    return whitespace(specific(s))


def gdex_examples(corp, query, number):
    """
    GDEX query
    :param corp_name: str
    :param query: str
    :param number: int
    :return: GDEX result object
    """
    gdex_engine = gdex.GDEX(corp)
    cc = PyConc(corp, 'q', query)
    cc.sync()
    gdex_engine.entryConc(cc)
    best_lines = manatee.IntVector([i for s,i in gdex_engine.best_k(number, max(number*10, 100))])

    cc.set_sorted_view(best_lines)
    return cc


def get_n_gdex_examples(query, corp, ref_corpname, number):
    """
    Extract N examples sentences sorted by GDEX score. If not enough examples in current corpus
    look to reference corpus
    :param query: str, query string
    :param corp: str
    :param ref_corpname: str
    :param number: int
    :return: list
    """
    corp_gdex_examples = gdex_examples(corp, query, number)

    out = []
    for line in strkwiclines(corp_gdex_examples, 0, number, '1:s', '1:s'):
        left = line['left']
        kwic = line['kwic']
        right = line['right']
        out.append((sentence(left + kwic + right), 'focus_corpus'))

    if len(out) < number:
        ref_corp = manatee.Corpus(ref_corpname)
        ref_corp_gdex_examples = gdex_examples(ref_corp, query, number)
        for line in strkwiclines(ref_corp_gdex_examples, 0, number - len(out), '1:s', '1:s'):
            left = line['left']
            kwic = line['kwic']
            right = line['right']
            out.append((sentence(left + kwic + right), 'reference_corpus'))

    return out


class ConcError (Exception):
    def __init__ (self, msg):
        self.message = msg
    def __str__ (self):
        return self.message


class ConcCGI (UserCGI):

    _global_vars = ['corpname', 'viewmode', 'attrs', 'attr_allpos', 'ctxattrs',
                    'structs', 'refs', 'lemma', 'lpos', 'pagesize',
                    'usesubcorp', 'align', 'gdex_enabled',
                    'gdexcnt', 'gdexconf', 'show_gdex_scores', 'iquery',
                    'maincorp', 'complement_subc', 'attr_tooltip']
    error = ''
    fc_lemword_window_type = 'both'
    fc_lemword_type = 'all'
    fc_lemword_wsize=5
    fc_lemword=''
    fc_pos_window_type = 'both'
    fc_pos_type = 'all'
    fc_pos_wsize=5
    fc_pos=[]
    ml = 0
    concarf = ''
    Aligned = []
    concsize = ''
    samplesize = 10000000 #10M
    fromp = '1'
    fromc = ''
    ml1icase = ''
    ml2icase = ''
    ml3icase = ''
    ml4icase = ''
    ml1bward = ''
    ml2bward = ''
    ml3bward = ''
    freq_sort = ''
    heading = 0
    saveformat = 'text'
    wlattr = ''
    wlpat = ''
    wlpage = 1
    wlcache = ''
    wlicase = 0
    blcache = ''
    simple_n = 1.0
    usearf = 0
    collpage = 1
    fpage = 1
    fmaxitems = 50
    ftt_include_empty = ''
    subcsize = 0
    processing = 0
    ref_usesubcorp = ''
    wlsort = 'frq'
    keywords = ''
    Keywords = []
    ref_corpname = ''
    Items = []
    selected = ''
    saved_attrs = 0
    # save options
    pages = 0
    leftctx = ''
    rightctx = ''
    numbering = 0
    align_kwic = 0
    righttoleft = False
    stored = ''
    # end

    corpname = 'susanne'
    corplist = ['susanne', 'bnc']
    usesubcorp = ''
    wlusesubcorp = ''
    obsolete_subcorp = ''
    obsolete_has_subcdef = False
    subcname = ''
    subcpath = []
    _conc_dir = ''
    annotation_group = ''
    _home_url = '../index.html'
    files_path = '..'
    css_prefix = ''
    logo_prefix = ''
    iquery = ''
    queryselector = 'iqueryrow'
    lemma = ''
    lpos = ''
    phrase = ''
    char = ''
    word = ''
    wpos = ''
    cql = ''
    default_attr = None
    save = 1
    asyn = 1
    qmcase = 0
    rlines = '250'
    attrs = 'word'
    ctxattrs = 'word'
    attr_allpos = 'kw'
    allpos = 'kw'
    attr_tooltip = 'nott'
    structs = 'p,g,err,corr'
    q = []
    pagesize = 20
    gdexconf = ''
    gdexpath = [] # [('confname', '/path/to/gdex.conf'), ...]
    gdexcnt = 0
    gdex_enabled = 0
    show_gdex_scores = 0
    alt_gdexconf = None
    _avail_tbl_templates = ''
    show_kwic_translations = 1
    wlsendmail = ''
    cup_hl = 'q'

    sortlevel=1
    flimit = 0
    freqlevel=1
    ml1pos = 1
    ml2pos = 1
    ml3pos = 1
    ml4pos = 1
    ml1ctx = '0~0>0'
    ml2ctx = '0~0>0'
    ml3ctx = '0~0>0'
    ml4ctx = '0~0>0'
    tbl_template = 'none'
    errcodes_link = ''
    hidenone = 1
    shorten_refs = 0
    err_types_select = False
    _majorversionerr = []
    _minorversionerr = []
    annotconc = ''

    # trends
    trends_re = ''
    trends_maxp = 0.1
    trends_method = 'mkts_all'
    trends_sort_by = 't'
    trends_minfreq = 5
    trends_order = 'desc'
    trends_attr = 'word'
    trends_max_items = 1000
    filter_by_trend = 0
    filter_nonwords = 1
    filter_capitalized = 1

    def __init__ (self):
        self.cm = corplib.CorpusManager (self.corplist, self.subcpath,
                                         self.gdexpath, self._job,
                                         abs_corpname=self.abs_corpname)
        self._curr_corpus = None

    def corpora(self):
        l = []
        defs = {
            'id': None,
            'owner_id': None,
            'owner_name': None,
            'tagset_id': None,
            'sketch_grammar_id': None,
            'term_grammar_id': None,
            '_is_sgdev': False,
            'is_featured': False,
            'access_on_demand': False,
            'terms_of_use': None,
            'sort_to_end': None,
            'tags': [],
            'created': None,
            'needs_recompiling': False,
            'user_can_read': True,
            'user_can_upload': False,
            'user_can_manage': False,
            'is_shared': False,
            'is_error_corpus': False
        }
        for c in self.corplist:
            o = dict(defs)
            try:
                mc = conclib.manatee.Corpus(self.abs_corpname(c))
                o.update({
                    'corpname': c,
                    'language_id': mc.get_conf('LANGUAGE'),
                    'language_name': mc.get_conf('LANGUAGE'),
                    'sizes': dict([x.split() for x in mc.get_sizes().split('\n')\
                            if len(x.split()) == 2]),
                    'compilation_status': mc.get_sizes() and 'COMPILED' or 'READY',
                    'new_version': mc.get_conf('NEWVERSION'),
                    'name': mc.get_conf('NAME'),
                    'info': mc.get_conf('INFO'),
                    'wsdef': mc.get_conf('WSDEF'),
                    'termdef': mc.get_conf('TERMDEF'),
                    'diachronic': bool(mc.get_conf('DIACHRONIC')),
                    'aligned': mc.get_conf('ALIGNED').split(',') if mc.get_conf('ALIGNED') else [],
                    'docstructure': mc.get_conf('DOCSTRUCTURE')
                })
                if '/' in c:
                    owner_name = c.split('/', 1)[0]
                    o.update({
                        'owner_id': owner_name,
                        'owner_name': owner_name
                    })
                l.append(o)
            except corplib.manatee.CorpInfoNotFound as e:
                pass
        return {'data': l}

    def languages(self):
        langs = set()
        for c in self.corplist:
            try:
                mc = conclib.manatee.Corpus(self.abs_corpname(c))
                lang = mc.get_conf('LANGUAGE')
            except corplib.manatee.CorpInfoNotFound:
                continue
            langs.add(lang)
        data = []
        for lang in langs:
            data.append({
                'id': lang,
                'name': lang,
                'default_tagset_id': None,
                'reference_corpus': None,
                'term_reference_corpus': None,
                'has_term_grammar': False,
            })
        return {'data': data}

    def abs_corpname(self, corpname):
        return corpname

    def now(self):
        return time.strftime('%Y-%m-%d_%H:%M:%S')

    def self_encoding(self):
        return (not self._curr_corpus is None) and self._curr_corpus.get_conf('ENCODING') or\
                (self._corp().get_conf('ENCODING') or "utf-8")

    def _corp (self):
        if (not self._curr_corpus or
            (self.usesubcorp and not hasattr(self._curr_corpus, 'subcname'))):
            self._curr_corpus = self.cm.get_Corpus (self.corpname,
                                         self.usesubcorp, self.complement_subc)
            if self.cm.obsolete_subcorp:
                self.obsolete_subcorp = self.cm.obsolete_subcorp
                self.obsolete_has_subcdef = self.cm.obsolete_has_subcdef
                if self.obsolete_has_subcdef:
                    self.rebuild_subc(self.usesubcorp)
            if self.cm.missing_subc_error:
                self.usesubcorp = ''
                raise RuntimeError(self.cm.missing_subc_error)
            # XXX opravit poradne!
            self._curr_corpus.annotation_group = self.annotation_group
            if self.annotation_group:
                if hasattr(self, "_annot_dir"):
                    self._curr_corpus._conc_dir = os.path.join(self._annot_dir,
                            self.annotation_group, self.corpname)
                else:
                    self._curr_corpus._conc_dir = os.path.join(self._conc_dir,
                            'skema', self.annotation_group, self.corpname)
            else:
                self._curr_corpus._conc_dir = self._conc_dir
        if self._user and self.user_gdex_path:
            self.cm.user_gdex_path = self.user_gdex_path % self._user
        return self._curr_corpus

    def _ensure_fsa (self, corplist, source, sourcetype):
        for corpus in corplist:
            cmd = corplib.has_fsa(corpus, source, sourcetype)
            if cmd: # non-None cmd indicates FSA missing, otherwise pair (cmd, desc) is returned
                return bgjob_info(corplib.run_bgjob(self._user, corpus, cmd[0], cmd[1], self.get_url()))

    def _ensure_ngrams (self, corplist, attr):
        import os
        for corpus in corplist:
            if not os.path.isfile(corpus.get_conf("PATH") + attr + ".ngr.rev"):
                return bgjob_info(corplib.compute_ngrams (self._user, corpus, attr, self.get_url()))

    def desc(self, conc=None):
        out = []
        conc_desc = conclib.get_conc_desc (self.q,
                          corpname=self.corpname, _cache_dir=self._cache_dir,
                          subchash=getattr(self._corp(), "subchash", None))
        csize = self._corp().search_size()
        for o,a,u1,u2,s,f,da in conc_desc:
            rel = ''
            if conc and s != '':
                fullsize = conc.fullsize()
                if float(s) == float(-1): # not computed yet
                    s = fullsize
                if (not out and s == self.samplesize # trimmed, show full size
                            and fullsize > self.samplesize):
                    s = fullsize
                rel = round(float(s) * 1000000.0 / csize, 2)
            out.append({'op': o, 'arg': a, 'nicearg': nicearg(a),
                                'rel': rel, 'size': s,
                                'tourl': self.urlencode(u2)})
        return out


    kwicleftctx = '40#'
    kwicrightctx = '40#'
    senleftctx = '-1:s'
    senrightctx = '1:s'
    viewmode = 'kwic'
    align = ''
    sel_aligned = []
    maincorp = ''
    refs_up = 0

    def set_default_refs (self):
        if 'refs' not in self.__dict__:
            if self._corp().get_conf('SHORTREF'):
                self.refs = self._corp().get_conf('SHORTREF')
            else:
                sal = self._corp().get_conf('STRUCTATTRLIST').split(',')
                docs = self._corp().get_conf('DOCSTRUCTURE')
                if docs + '.urldomain' in sal:
                    self.refs = '=' + docs + '.urldomain'
                else:
                    self.refs = '#'
        if 'reflinks' not in self.__dict__:
            c = self._corp()
            sal = c.get_conf('STRUCTATTRLIST').split(',')
            for sa in sal:
                if sa and c.get_conf(sa + '.URLTEMPLATE'):
                    self.reflinks.append(sa)

    reflinks = []
    concordance_query = []

    def process_concordance_query(self):
        for obj in self.concordance_query:
            if 'q' in obj:
                if obj['q'].startswith('e') and self.show_gdex_scores:
                    self.q.append('E' + obj['q'][1:])
                else:
                    self.q.append(obj['q'])
            else:
                correct_types(obj, self.defaults)
                for k, v in list(obj.items()): # set attributes
                    setattr(self, k, v)
                if 'pnfilter' in obj: # filter
                    self.q.append(self.filter(return_q=True))
                elif 'sattr' in obj: # simple sort
                    self.q.append(self.sortx(return_q=True))
                elif 'mlsort_options' in obj: # multilevel sort
                    self.q.append(multilevel_sort_crit(obj['mlsort_options']))
                else: # first form
                    self.set_first_query()
                    if obj.get('random', 0):
                        self.q[0] = 'R' + self.q[0]
                for k, v in list(obj.items()): # clean up
                    if k in self.defaults: setattr(self, k, self.defaults[k])
                    else: delattr(self, k)

    def reformat_conc_line(self, line):
        for k in ['Left', 'Kwic', 'Right']:
            split = (k == 'Kwic' and not ',' in self.attrs) or \
                    (k != 'Kwic' and not ',' in self.ctxattrs)
            newsegments = []
            for i, segment in enumerate(line[k]):
                newsegment = {}
                if segment['class'] == 'strc':
                    newsegment['strc'] = segment['str']
                elif 'coll' in segment['class']:
                    newsegment['coll'] = 1
                    newsegment['str'] = segment['str']
                    if re.search(r'coll\d+', segment['class']):
                        newsegment['coll_label'] = int(re.search(r'coll(\d+)', segment['class']).group(1))
                elif segment['class'] == 'attr' and i>0:
                    newsegments[-1]['attr'] = segment['str']
                elif '#' in segment['class']:
                    c = [x for x in segment['class'].split() if x.startswith('#')][0]
                    newsegment['color'] = c
                    newsegment['str'] = segment['str']
                    rem = segment['class'].replace(c, '').strip()
                    if rem:
                        newsegment['class'] = rem
                elif 'conc' in segment['class']:
                    c = [x for x in segment['class'].split() if x.startswith('conc')][0]
                    newsegment['color'] = c[4:]
                    newsegment['str'] = segment['str']
                    rem = segment['class'].replace(c, '').strip()
                    if rem:
                        newsegment['class'] = rem
                else:
                    newsegment['str'] = segment['str']
                if newsegment and split:
                    if 'str' in newsegment: str_c = 'str'
                    else: str_c = 'strc'
                    keys = [x for x in list(newsegment.keys())
                              if x not in ('str', 'strc')]
                    parts = [{str_c: x} for x in newsegment[str_c].split()]
                    for part in parts:
                        for key in keys:
                            part[key] = newsegment[key]
                    newsegments += parts
                elif newsegment:
                        newsegments.append(newsegment)
            line[k] = newsegments

    def get_ref_list(self):
        """
        Computes list of all possible struc.attr values to be able to export only the required columns
        return: list of struct.attr
        """
        result = []
        for struct in self.corp_info()['structures']:
            for attr in struct['attributes']:
                result.append(struct['name'] + '.' + attr['name'])
        return result

    def concordance (self):
        "concordance API for Platypus"
        self.format = self.format or 'json'
        self.process_concordance_query()
        self.gdex_enabled = 0 # fix for Crystal, might be removed later
        out = self.view()
        if 'error' in out:
            out.update({'concsize': 0, 'fullsize': 0, 'Lines': []})
            return out
        for line in out['Lines']: # reformat the output
            self.reformat_conc_line(line)
            for aligned_line in line.get('Align', []):
                self.reformat_conc_line(aligned_line)
        return out

    def view (self):
        "kwic view"

        # attr_allpos: all attrs should be applied to all resulting tokens (left and right), default "word"
        if self.attr_allpos == 'all':
            self.ctxattrs = self.attrs

        self.set_default_refs()
        if self._corp().get_conf('RIGHTTOLEFT') == '1':
            self.righttoleft = True
        if self.viewmode == 'kwic':
            self.leftctx = self.kwicleftctx
            self.rightctx = self.kwicrightctx
        elif self.viewmode == 'align' and self.align:
            self.leftctx = 'a,%s' % os.path.basename(self.corpname)
            self.rightctx = 'a,%s' % os.path.basename(self.corpname)
        else:
            self.leftctx = self.senleftctx
            self.rightctx = self.senrightctx
        # simplified querying of parallel corpora
        if getattr(self, 'l1q', False):
            l1q = getattr(self, 'l1q', '').strip().lower().split()
            l2q = getattr(self, 'l2q', '').strip().lower().split()
            c1 = getattr(self, 'c1', self.corpname)
            c2 = getattr(self, 'c2', '')
            if ''.join(l1q):
                self.q = ['q[lc="' + '"][lc="'.join(l1q) + '"]']
                if ''.join(l2q):
                    self.q[0] += ' within %s: ' % c2
                    self.q[0] += '[lc="' + '"][lc="'.join(l2q) + '"]'
            elif ''.join(l2q):
                self.q = ['q[lc="' + '"][lc="'.join(l2q) + '"]']
                c1, c2 = c2, c1
                self.align = c1
                self.maincorp = c2
            self.q.append('X%s' % c1)

        # GDEX roundabouts
        if self.show_gdex_scores: op = 'E'
        else: op = 'e'
        if self.gdex_enabled and self.gdexcnt: # backward compatibility
            self.q.append('%s%s %s' % (op, str(self.gdexcnt), self.gdexconf))
        for ii, qq in enumerate(self.q): # API use
            if qq.startswith('s*'):
                self.q[ii] = op + qq[2:]

        conc = self.call_function (conclib.get_conc, (self._corp(),))

        if not conc.size():
            return {'Lines': [], 'finished': 1, 'concsize': 0, 'fullsize': 0,
                    'asyn': 0, 'Desc': self.desc(conc)}
        conc.switch_aligned (os.path.basename(self.corpname))
        labelmap = {}
        concordance_size_limit = 10 * self._wordlist_max_size
        if self.annotconc:
            if os.path.exists(self._storeconc_path() + '.conc'):
                annot = self.get_stored_conc()
                conc.set_linegroup_from_conc(annot)
                labelmap = annot.labelmap
            else:
                self.annotconc = ''
        elif self._wordlist_max_size > 0:
            self.pagesize = min(self.pagesize, concordance_size_limit)
        alignlist = [self.cm.get_Corpus(c) for c in self.align.split(',') if c]
        out = self.call_function(conclib.kwicpage, (conc,), labelmap=labelmap,
                                 pagesize=self.pagesize,
                                 alignlist=alignlist,
                                 tbl_template=self.tbl_template,
                                 reflinks=self.reflinks)
        out['concordance_size_limit'] = concordance_size_limit
        if self.annotconc:
            out['Sort_idx'] = []
        else:
            out['Sort_idx'] = self.call_function (conclib.get_sort_idx, (conc,),
                                                      enc=self.self_encoding())
        out['righttoleft'] = self.righttoleft
        out['Aligned_rtl'] = [x.get_conf('RIGHTTOLEFT') == "1" for x in alignlist]
        out['numofcolls'] = conc.numofcolls()
        # get sizes
        relsize = float(1000000) * conc.fullsize() / conc.corp().search_size()
        out.update({'concsize': not self.error and conc.size() or 0,
                    'finished': int(conc.finished()),
                    'fullsize': conc.fullsize(),
                    'relsize': round(relsize, 2) })
        docstruct = conc.corp().get_conf("DOCSTRUCTURE")
        starattr = conc.corp().get_conf("STARATTR")
        if docstruct and starattr and conc.finished():
            star, docf = conclib.manatee.calc_average_structattr(conc.corp(), docstruct, starattr, conc.RS())
            sc = self.cm.get_Corpus (self.corpname, self.usesubcorp)
            size = sc.get_struct(sc.get_conf("DOCSTRUCTURE")).search_size()
            out.update({"star": star, "docf": docf, 'reldocf': round(docf * 100 / size, 5)})
        if self._corp().get_conf ('ALIGNED'):
            out['Aligned'] = [{'n': w,
                               'label': conclib.manatee.Corpus(w).get_conf(
                                                                  'NAME') or w }
                         for w in self._corp().get_conf ('ALIGNED').split(',')]
        if self.align and not self.maincorp:
            self.maincorp = os.path.basename(self.corpname)
        out['q'] = self.q
        out['Desc'] = self.desc(conc)
        out['port'] = conc.port
        out['gdex_scores'] = conc.gdex_scores
        out['sc_strcts'] = [(st, self._corp().get_conf(st + '.LABEL') or st)
                for st in self._corp().get_conf('STRUCTLIST').split(',') if st]
        return out


    def struct_attr_values(self, struct, attr):
        try:
            a = self._corp().get_struct(struct).get_attr(attr)
            return sorted([a.id2str(i) for i in range(a.id_range()) if a.freq(i) > 0])
        except:
            return []


    def get_conc_sizes (self, q=[], port=0):
        self._headers['Content-Type']= 'text/plain'
        cs = self.call_function (conclib.get_conc_sizes, (self._corp(),),
                                 q=q or self.q, server_port=port)
        return "\n".join(map(str,[cs["finished"], cs["concsize"],
                                  cs["relconcsize"], cs["fullsize"]]))

    def concdesc (self):
        return {'Desc': [{'op': o, 'arg': a, 'churl': self.urlencode(u1), 'da': da,
                          'tourl': self.urlencode(u2), 'size': s, 'formname': f}
                         for o, a, u1, u2, s, f, da in
                         conclib.get_conc_desc (self.q,
                                                corpname=self.corpname,
                                                _cache_dir=self._cache_dir,
                                                subchash=getattr(self._corp(),
                                                             "subchash", None))]
                }

    # sortx options
    sattr = 'word'
    spos = 3
    skey = 'rc'
    sicase = ''
    sbward = ''
    def sortx (self, return_q=False):
        "simple sort concordance"
        if self.skey == 'lc':
            ctx = '-1<0~-%i<0' % self.spos
        elif self.skey == 'kw':
            ctx = '0<0~0>0'
        elif self.skey == 'rc':
            ctx = '1>0~%i>0' % self.spos
        if '.' in self.sattr:
            ctx = ctx.split('~')[0]
        lastq = 's%s/%s%s %s' % (self.sattr, self.sicase, self.sbward, ctx)
        if return_q:
            return lastq
        self.q.append (lastq)
        return self.view()

    def mlsortx (self,
          ml1attr='word', ml1pos=1, ml1icase='', ml1bward='', ml1fcode='rc',
          ml2attr='word', ml2pos=1, ml2icase='', ml2bward='', ml2fcode='rc',
          ml3attr='word', ml3pos=1, ml3icase='', ml3bward='', ml3fcode='rc',
          sortlevel=1, ml1ctx='', ml2ctx='', ml3ctx=''):
        "multiple level sort concordance"
        # obsolete, replaced with multilevel_sort for Platypus

        crit = onelevelcrit ('s', ml1attr, ml1ctx, ml1pos, ml1fcode,
                             ml1icase, ml1bward)
        if sortlevel > 1:
            crit += onelevelcrit (' ', ml2attr, ml2ctx, ml2pos, ml2fcode,
                                  ml2icase, ml2bward)
            if sortlevel > 2:
                crit += onelevelcrit (' ', ml3attr, ml3ctx, ml3pos, ml3fcode,
                                      ml3icase, ml3bward)
        self.q.append (crit)
        return self.view()

    def is_err_corpus(self):
        availstruct = self._corp().get_conf('STRUCTLIST').split(',')
        if not ('err' in availstruct and 'corr' in availstruct):
            return False
        return True

    def _compile_basic_query (self, qtype=None, suff='', cname=''):
        queryselector = getattr(self, 'queryselector' + suff)
        iquery = ''
        if queryselector == 'iqueryrow':
            iquery = getattr(self, 'iquery' + suff, '').strip()
            if iquery == '\\':
                iquery = '\\\\'
            iquery = re.sub(r'\\([^.?\\*])', r'\1', iquery)
            iquery = iquery.replace('\\.', '\v')
            iquery = iquery.replace('.', '\\.').replace('\v', '\\.')
            iquery = iquery.replace('\\?', '\v').replace('?', '.')
            iquery = iquery.replace('\v', '?').replace('\\*', '\v')
            iquery = iquery.replace('*', '.*').replace('\v', '\\*')
        lemma = getattr(self, 'lemma' + suff, '')
        lpos = getattr(self, 'lpos' + suff, '')
        phrase = getattr(self, 'phrase' + suff, '')
        qmcase = getattr(self, 'qmcase' + suff, '')
        word = getattr(self, 'word' + suff, '')
        wpos = getattr(self, 'wpos' + suff, '')
        char = getattr(self, 'char' + suff, '')
        cql = getattr(self, 'cql' + suff, '')
        queries = {
            'cql': '%(cql)s',
            'lemma': '[lempos="%(lemma)s%(lpos)s"]',
            'wordform': '[%(wordattr)s="%(word)s" & tag="%(wpos)s.*"]',
            'wordformonly': '[%(wordattr)s="%(word)s"]',
            }
        for a in ('iquery', 'word', 'lemma', 'phrase', 'cql', 'char'):
            if queryselector == a + 'row':
                if getattr(self, a+suff, ''):
                    setattr (self, a+suff, getattr (self, a+suff).strip())
                elif suff:
                    return ''
                else:
                    raise ConcError('No query entered.')
        if qtype:
            return queries[qtype] % self.clone_self()
        thecorp = cname and self.cm.get_Corpus (cname) or self._corp()
        attrlist = thecorp.get_conf('ATTRLIST').split(',')
        wposlist = dict (corpconf_pairs (thecorp, 'WPOSLIST'))
        lposlist = dict (corpconf_pairs (thecorp, 'LPOSLIST'))
        if queryselector == 'iqueryrow':
            qitem = thecorp.get_conf('SIMPLEQUERY').replace('%s', '%(q)s')
            if '--' not in iquery:
                iqresult = ''
                for iqpart in iquery.split('|'):
                    if iqresult:
                        iqresult += ' | '
                    iqresult += ''.join([qitem % {'q':escape_nonwild(q)}
                                         for q in iqpart.split()])
                return iqresult
            else:
                def split_tridash (word, qitem):
                    if '--' not in word:
                          return qitem % {'q':word}
                    w1,w2 = word.split('--',1)
                    return "( %s | %s %s | %s )" % (qitem % {'q':w1+w2},
                                                    qitem % {'q':w1},
                                                    qitem % {'q':w2},
                                                    qitem % {'q':w1+'-'+w2})
                return ''.join([split_tridash(escape_nonwild(q), qitem)
                                for q in iquery.split()])

        if queryselector == 'lemmarow':
            if not lpos:
                if qmcase:
                    return '[lemma="%s"]' % lemma
                else:
                    if 'lemma_lc' in attrlist:
                        return '[lemma_lc="%s"]' % lemma
                    else:
                        return '[lemma="(?i)%s"]' % lemma
            if 'lempos' in attrlist:
                try:
                    if not lpos in list(lposlist.values()):
                        lpos = lposlist [lpos]
                except KeyError:
                    raise ConcError ('Undefined lemma PoS' + ' "%s"' % lpos)
                if qmcase:
                    return '[lempos="(%s)%s"]' % (lemma, lpos)
                else:
                    if 'lempos_lc' in attrlist:
                        return '[lempos_lc="(%s)%s"]' % (lemma, lpos)
                    else:
                        return '[lempos="(?i)(%s)%s"]' % (lemma, lpos)
            else: # XXX
                try:
                    if lpos in list(wposlist.values()):
                        wpos = lpos
                    else:
                        wpos = wposlist [lpos]
                except KeyError:
                    raise ConcError ('Undefined word form PoS' + ' "%s"' % lpos)
                if qmcase:
                    return '[lemma="%s" & tag="%s"]' % (lemma, wpos)
                else:
                    if 'lemma_lc' in attrlist:
                        return '[lemma_lc="%s" & tag="%s"]' % (lemma, wpos)
                    else:
                        return '[lemma="(?i)%s" & tag="%s"]' % (lemma, wpos)
        if queryselector == 'phraserow':
            if qmcase:
                return ' | '.join(['"' + '" "'.join(phr.split()) + '"'
                        for phr in phrase.split('|')])
            else:
                if "lc" in attrlist:
                    return ' | '.join([" ".join(['[lc="%s"]' % x for x in phr.split()])
                            for phr in phrase.split('|')])
                else:
                    return ' | '.join([" ".join(['[word="(?i)%s"]' % x for x in phr.split()])
                            for phr in phrase.split('|')])
        if queryselector == 'wordrow':
            if qmcase:
                wordattr = 'word="%s"' % word
            else:
                if 'lc' in attrlist:
                    wordattr = 'lc="%s"' % word
                else:
                    wordattr = 'word="(?i)%s"' % word
            if not wpos:
                return '[%s]' % wordattr
            try:
                if not wpos in list(wposlist.values()):
                    wpos = wposlist [wpos]
            except KeyError:
                raise ConcError ('Undefined word form PoS' + ' "%s"' % wpos)
            return '[%s & tag="%s"]' % (wordattr, wpos)
        if queryselector == 'charrow':
            if not char: raise ConcError('No char entered')
            return '[word=".*%s.*"]' % escape(char)
        return cql


    def _compile_query(self, qtype=None, cname=''):
        if not self.is_err_corpus():
            return self._compile_basic_query(qtype, cname=cname)
        err_code = getattr(self, 'cup_err_code', '')
        err = getattr(self, 'cup_err', '')
        corr = getattr(self, 'cup_corr', '')
        switch = getattr(self, 'errcorr_switch', '')
        if not err_code and not err and not corr:
            cql = self._compile_basic_query(qtype)
            if self.queryselector != 'cqlrow':
                cql = cql.replace('][', '] (<corr/>)? [')
                cql = cql.replace('](', '] (<corr/>)? (')
                cql = cql.replace('] [', '] (<corr/>)? [')
            return cql
        # compute error query
        # Achtung: Top error lists (method freq) depends on this -- do check it
        # when changing the below
        corr_restr = corr or (err_code and switch == 'c')
        err_restr = err or (err_code and switch == 'e')
        if err_code: corr_within = '<corr type="%s"/>' % err_code
        else: corr_within = '<corr/>'
        if err_code: err_within = '<err type="%s"/>' % err_code
        else: err_within = '<err/>'
        err_containing = ''; corr_containing = ''
        if err:
            self.iquery = err; self.queryselector = 'iqueryrow'
            err_containing = ' containing ' + self._compile_basic_query(qtype)
        if corr:
            self.iquery = corr; self.queryselector = 'iqueryrow'
            corr_containing = ' containing ' + self._compile_basic_query(qtype)
        err_query =  '(%s%s)' % (err_within, err_containing)
        corr_query = '(%s%s)' % (corr_within, corr_containing)
        fullstruct = '(%s%s)' % (err_query, corr_query)
        if self.cup_hl == 'e' or (self.cup_hl == 'q' and err_restr
                                                     and not corr_restr):
            return '%s within %s' % (err_query, fullstruct)
        elif self.cup_hl == 'c' or (self.cup_hl == 'q' and corr_restr
                                                       and not err_restr):
            return '%s within %s' % (corr_query, fullstruct)
        else: # highlight both
            return fullstruct

    def query (self, qtype='cql'):
        "perform query"
        if self.default_attr:
            qbase = 'a%s,' % self.default_attr
        else:
            qbase = 'q'
        self.q = [qbase + self._compile_query()]
        return self.view()

    def set_first_query (self):
        def append_filter (attrname, items, ctx, fctxtype):
            if not items:
                return
            if fctxtype == 'any':
                self.q.append ('P%s [%s]' %
                               (ctx, '|'.join (['%s="%s"' % (attrname, i)
                                                for i in items])))
            elif fctxtype == 'none':
                self.q.append ('N%s [%s]' %
                          (ctx, '|'.join (['%s="%s"' % (attrname, i)
                                           for i in items])))
            elif fctxtype == 'all':
                for i in items:
                    self.q.append ('P%s [%s="%s"]' % (ctx, attrname, i))

        if 'lemma' in self._corp().get_conf('ATTRLIST').split(','):
            lemmaattr = 'lemma'
        else:
            lemmaattr = 'word'
        wposlist = dict (corpconf_pairs (self._corp(), 'WPOSLIST'))
        if self.queryselector == 'phraserow':
            self.default_attr = 'word' # XXX to be removed with new first form
        if self.default_attr:
            qbase = 'a%s,' % self.default_attr
        else:
            qbase = 'q'
        texttypes = self._texttype_query()
        if texttypes:
            ttquery = ' ' + ' '.join (['within <%s %s />' % nq for nq in texttypes])
        else:
            ttquery = ''
        par_query = ''
        nopq = []
        for al_corpname in self.sel_aligned:
            if getattr(self, 'pcq_pos_neg_' + al_corpname) == 'pos': wnot = ''
            else: wnot = '!'
            pq = self._compile_basic_query(suff='_'+al_corpname,
                                           cname=al_corpname)
            if pq: par_query += ' within%s %s:%s' % (wnot, al_corpname, pq)
            if not pq or wnot: nopq.append(al_corpname)
        self.q = [qbase + self._compile_query() + ttquery + par_query]

        if self.fc_lemword_window_type == 'left':
            append_filter (lemmaattr,
                           self.fc_lemword.split(),
                           '-%i -1 -1' % self.fc_lemword_wsize,
                           self.fc_lemword_type)
        elif self.fc_lemword_window_type == 'right':
            append_filter (lemmaattr,
                           self.fc_lemword.split(),
                           '1 %i 1' % self.fc_lemword_wsize,
                           self.fc_lemword_type)
        elif self.fc_lemword_window_type == 'both':
            append_filter (lemmaattr,
                           self.fc_lemword.split(),
                           '-%i %i 1' % (self.fc_lemword_wsize,
                                         self.fc_lemword_wsize),
                           self.fc_lemword_type)
        if self.fc_pos_window_type == 'left':
            append_filter ('tag',
                           [wposlist.get(t,'') for t in self.fc_pos],
                           '-%i -1 -1' % self.fc_pos_wsize,
                           self.fc_pos_type)
        elif self.fc_pos_window_type == 'right':
            append_filter ('tag',
                           [wposlist.get(t,'') for t in self.fc_pos],
                           '1 %i 1' % self.fc_pos_wsize,
                           self.fc_pos_type)
        elif self.fc_pos_window_type == 'both':
            append_filter ('tag',
                           [wposlist.get(t,'') for t in self.fc_pos],
                           '-%i %i 1' % (self.fc_pos_wsize, self.fc_pos_wsize),
                           self.fc_pos_type)
        for al_corpname in self.sel_aligned:
            if al_corpname in nopq and getattr(self,
                                         'filter_nonempty_' + al_corpname, ''):
                self.q.append('X%s' % al_corpname)
        if self.sel_aligned: self.align = ','.join(self.sel_aligned)


    def first (self):
        self.set_first_query()
        return self.view()

    # filter settings
    pnfilter = 'p'
    partial_match = 1
    filfpos = '-5'
    filtpos = '5'
    within = 0
    inclkwic = False

    def filter (self, return_q=False):
        "Positive/Negative filter"
        if not self.inclkwic:
            self.pnfilter = self.pnfilter.upper()
        rank = self.partial_match 
        texttypes = self._texttype_query()
        try:
            query = self._compile_basic_query(cname=self.maincorp)
        except ConcError:
            if texttypes: query = '[]'; self.filfpos='0'; self.filtpos='0'
            else: raise ConcError ('No query entered.')
        query +=  ' '.join (['within <%s %s />' % nq for nq in texttypes])
        if self.within:
            kw = self.pnfilter in 'nN' and ' within! ' or ' within '
            wquery =  kw + '%s:(%s)' % (self.maincorp or self.corpname, query)
            self.q[0] += wquery
            lastq = 'x-' + (self.maincorp or self.corpname)
        else:
            lastq = '%s%s %s %i %s' % (self.pnfilter, self.filfpos,
                                       self.filtpos, rank, query)
        if return_q:
            return lastq
        self.q.append(lastq)
        try:
            return self.view()
        except:
            if self.within: self.q[0] = self.q[0][:-len(wquery)]
            else: del self.q[-1]
            raise


    def reduce (self, rlines='250'):
        "random sample"
        self.q.append ('r' + rlines)
        return self.view()

    fcrit = []
    examples = 0
    group = 0
    hitlen = 0
    def freqs(self, fcrit=[], flimit=0, freq_sort='', ml=0):
        "display a frequency list"
        import operator
        def parse_fcrit(fcrit):
            attrs, marks, ranges = [], [], []
            for i, item in enumerate(fcrit.split()):
                if i % 2 == 0: attrs.append(item)
                if i % 2 == 1: ranges.append(item)
            return attrs, ranges
        if self._wordlist_max_size:
            if not self.fmaxitems:
                self.fmaxitems = self._wordlist_max_size
            else:
                self.fmaxitems = min(self.fmaxitems, self._wordlist_max_size)
        elif not self.fmaxitems:
            self.fmaxitems = 10000000
        corp = self._corp()
        csize = corp.search_size()
        if self.concordance_query: self.process_concordance_query()
        conc = self.call_function (conclib.get_conc, (corp, self.samplesize), asyn=0)
        if not self.hitlen:
            kwcls = self.call_function(conclib.kwicpage, (conc,))['Lines']
            if len(kwcls):
                self.hitlen = max([line['hitlen'] for line in kwcls])
                
        # For freqml computed on multiple attributes this is not appicable
        for cr in fcrit:
            attr = cr.split()[0].split('/')[0]
            if not '.' in attr:
                continue
            missing_norms = not corplib.are_subcorp_stats_compiled(corp, attr,
                                                                   'token:l')
            if missing_norms:
                subcpath = getattr(self._corp(), 'spath', '')
                return corplib.compute_norms(self._corp(), self._user,
                                  attr.split('.')[0], subcpath, self.get_url())
        result = {'fcrit': self.urlencode ([('fcrit', self.rec_recode(cr))
                                            for cr in fcrit]),
                  'FCrit': [{'fcrit': cr} for cr in fcrit],
                  'Blocks': [conc.xfreq_dist (cr, flimit, freq_sort, ml,
                             self.ftt_include_empty, self.wlmaxfreq) for cr in fcrit],
                  'paging': 0,
                  'concsize':conc.size(),
                  'fullsize':conc.fullsize(),
                  'Desc': self.desc(conc),
                  'numofcolls': conc.numofcolls(),
                  'hitlen': self.hitlen,
                  'wllimit': self._wordlist_max_size }
        if not result['Blocks'][0]:
            return result
        if len(result['Blocks']) == 1 and self.group:
            result['Blocks'][0]['Items'] = group_freqs_result(
                                                    result['Blocks'][0]['Items'])
        if len(result['Blocks']) == 1 and not self.examples: # paging
            fstart = (self.fpage - 1) * self.fmaxitems
            self.fmaxitems = self.fmaxitems * self.fpage + 1
            result['paging'] = 1
            if len(result['Blocks'][0]['Items']) < self.fmaxitems:
                result['lastpage'] = 1
            else:
                result['lastpage'] = 0
            result['Blocks'][0]['Items'] = \
               result['Blocks'][0]['Items'][fstart:self.fmaxitems-1]
        for b in result['Blocks']:
            if self._wordlist_max_size and (self._wordlist_max_size
                                                 < len(b['Items'])):
                b['Items'] = b['Items'][:self._wordlist_max_size]
                result['lastpage'] = 1
                b['note'] = 'You are allowed to see only %s items.' \
                               % self._wordlist_max_size
            for item in b['Items']:
                item['pfilter'], item['nfilter'] = '', ''
                item['pfilter_list'] = []
                item['poc'] = (item.get('frq', 0) / float(conc.size())) * 100  # 10M restriction: conc.size() instead of conc.fullsize()
                item['fpm'] = (item.get('frq', 0) / float(csize)) * 1000000
                if conc.size() < conc.fullsize():  # 10M restriction: fpm value does not correspond to reality use "poc" instead
                    item['fpm'] = 0
                    
        ## generating positive and negative filter references
        for b_index, block in enumerate(result['Blocks']):
            curr_fcrit = fcrit[b_index]
            attrs, ranges = parse_fcrit(curr_fcrit)
            for level, (attr, range) in enumerate(zip(attrs, ranges)):
                begin = range.split('~')[0]
                if '~' in range: end = range.split('~')[1]
                else: end = begin
                attr = attr.split("/")
                if len(attr) > 1 and "i" in attr[1]: icase = '(?i)'
                else: icase = ''
                attr = attr[0]
                for ii, item in enumerate(block['Items']):
                    if not item['frq']: continue
                    if not '.' in attr:
                        if attr in corp.get_conf('ATTRLIST').split(','):
                            wwords = item['Word'][level]['n'].split('  ') # two spaces
                            fquery = '%s %s 0 ' % (begin, end)
                            fquery += ''.join(['[%s="%s%s"]'
                                % (attr, icase, escape(w)) for w in wwords ])
                        else: # structure number
                            if '#' in item['Word'][0]['n']:
                                fquery = '0 0<0 1 [] within <%s #%s/>' % \
                                      (attr, item['Word'][0]['n'].split('#')[1])
                            else:
                                fquery = '0 0<0 1 [] !within <%s/>' % attr
                    else: # text types
                        structname, attrname = attr.split('.')
                        if corp.get_conf(structname + '.NESTED'):
                            block['unprecise'] = True
                        fquery = '0 0<0 1 [] within <%s %s="%s" />' \
                                 % (structname, attrname,
                                    escape(item['Word'][level]['n']))
                    if not item['frq']: continue
                    efquery = self.urlencode(fquery)
                    item['pfilter'] += ';q=p%s' % efquery
                    item['pfilter_list'].append('p%s' % fquery)
                    if len(attrs) == 1 and item['frq'] <= conc.size():
                        item['nfilter'] += ';q=n%s' % efquery
        # adding no error, no correction (originally for CUP)
        errs, corrs, err_block, corr_block = 0, 0, -1, -1
        for b_index, block in enumerate(result['Blocks']):
           curr_fcrit = fcrit[b_index]
           if curr_fcrit.split()[0] == 'err.type':
               err_block = b_index
               for item in block['Items']: errs += item['frq']
           elif curr_fcrit.split()[0] == 'corr.type':
               corr_block = b_index
               for item in block['Items']: corrs += item['frq']
        freq = conc.size() - errs - corrs
        if freq > 0 and err_block > -1 and corr_block > -1:
            pfilter = ';q=p0 0<0 1 ([] within ! <err/>) within ! <corr/>'
            cc = self.call_function(conclib.get_conc, (corp,),
                                    q=self.q + [pfilter[3:]])
            freq = cc.size()
            err_nfilter, corr_nfilter = '', ''
            if freq != conc.size():
                err_nfilter = ';q=p0 0<0 1 ([] within <err/>) within ! <corr/>'
                corr_nfilter = ';q=p0 0<0 1 ([] within! <err/>) within <corr/>'
            result['Blocks'][err_block]['Items'].append(
                              {'Word': [{'n': 'no error' }], 'frq': freq,
                               'pfilter': pfilter, 'nfilter': err_nfilter,
                               'norel': 1, 'fbar' :0} )
            result['Blocks'][corr_block]['Items'].append(
                         {'Word': [{'n': 'no correction' }], 'frq': freq,
                          'pfilter': pfilter, 'nfilter': corr_nfilter,
                          'norel': 1, 'fbar' :0} )
        if self.format != 'json': 
            result['ref_list'] = self.get_ref_list()
        return result

    def freqml (self, flimit=0, freqlevel=1,
                ml1attr='word', ml1pos=1, ml1icase='', ml1fcode='rc',
                ml2attr='word', ml2pos=1, ml2icase='', ml2fcode='rc',
                ml3attr='word', ml3pos=1, ml3icase='', ml3fcode='rc',
                ml4attr='word', ml4pos=1, ml4icase='', ml4fcode='rc',
                ml5attr='word', ml5pos=1, ml5icase='', ml5fcode='rc',
                ml6attr='word', ml6pos=1, ml6icase='', ml6fcode='rc',
                ml1ctx='0', ml2ctx='0', ml3ctx='0', ml4ctx='0', ml5ctx='0',
                ml6ctx='0', ml1bwarde=1, ml2bwarde=1, ml3bwarde=1,
                ml4bwarde=1, ml5bwarde=1, ml6bwarde=1):
        "multilevel frequency list"
        l = locals()
        fcrit = ' '.join([onelevelcrit ('', l['ml%dattr'%i], l['ml%dctx'%i], l['ml%dpos'%i], 
                                        l['ml%dfcode'%i], l['ml%dicase'%i], 
                                        'e' if l['ml%dbwarde'%i] == 1 else '') for i in range(1, freqlevel+1)])
        ml = '.' not in ml1attr
        result = self.freqs([fcrit], flimit, self.freq_sort, ml)
        result['ml'] = ml
        return result

    def freqtt (self, flimit=0, fttattr=[]):
        if not fttattr:
            raise ConcError('No text type selected')
        return self.freqs (['%s 0' % a for a in fttattr], flimit)

    cattr = 'word'
    csortfn = 'd'
    cbgrfns = 'mtd'
    cfromw = -5
    ctow = 5
    cminfreq = 5
    cminbgr = 3
    cmaxitems = 50
    def collx (self, cattr='', csortfn='d', cbgrfns=['t','m', 'd'], usesubcorp=''):
        "list collocations"
        corp = self._corp() # !! must precede manatee.Corpus(maincorp)
        if self.maincorp:
            corp = conclib.manatee.Corpus(self.abs_corpname(self.maincorp))
        if usesubcorp and not corplib.are_subcorp_stats_compiled (corp, cattr):
            out = corplib.compute_freqfile (self._user, corp, cattr,
                                            self.wlnums, self.get_url())
            if out:
                return { 'processing': out["progress"] == '100' and '99' \
                                       or out["progress"],
                         'bgjob_notification': out['notifyme'] and 'checked' or '',
                         'jobid': out["jobid"], 'esttime': out["esttime"],
                         'new_maxitems': self.wlmaxitems, 'desc': out["desc"]}
        if self._wordlist_max_size:
            if not self.cmaxitems:
                self.cmaxitems = self._wordlist_max_size
            else:
                self.cmaxitems = min(self.cmaxitems, self._wordlist_max_size)
        elif not self.cmaxitems:
            self.cmaxitems = 10000000
        collstart = (self.collpage - 1) * self.cmaxitems
        self.cmaxitems = self.cmaxitems * self.collpage + 1
        self.cbgrfns = ''.join (cbgrfns)
        if not csortfn and cbgrfns:
            self.csortfn = cbgrfns[0]
        if self.concordance_query: self.process_concordance_query()
        conc = self.call_function (conclib.get_conc, (self._corp(),), asyn=0)
        result = self.call_function (conc.collocs, ())
        if len(result['Items']) < self.cmaxitems:
            result['lastpage'] = 1
        else:
            result['lastpage'] = 0;
            result['Items'] = result['Items'][:-1]
        result['wllimit'] = self._wordlist_max_size
        if result['wllimit'] and (result['wllimit'] < len(result['Items'])):
                result['Items'] = result['Items'][:self._wordlist_max_size]
                result['lastpage'] = 1
                result['note'] = 'You are allowed to see only %s items.' \
                                 % self._wordlist_max_size
        result['Items'] = result['Items'][collstart:]
        for item in result['Items']:
            item["pfilter"] = 'q=' + self.urlencode(item["pfilter"])
            item["nfilter"] = 'q=' + self.urlencode(item["nfilter"])
        result['concsize'] = conc.size()
        result['Desc'] = self.desc(conc)
        return result

    def structctx (self, pos=0, struct='doc'):
        "display a hit in a context of a structure"
        s = self._corp().get_struct(struct)
        struct_id = s.num_at_pos(pos)
        beg, end = s.beg(struct_id), s.end(struct_id)
        self.detail_left_ctx = pos - beg
        self.detail_right_ctx = end - pos - 1
        result = self.widectx(pos)
        result ['no_display_links'] = True
        return result

    def widectx (self, pos=0):
        "display a hit in a wider context"
        return self.call_function (conclib.get_detail_context, (self._corp(),
                                                                pos))

    def fullref (self, pos=0):
        "display a full reference"
        return self.call_function (conclib.get_full_ref, (self._corp(), pos))

    def freq_distrib(self, fcrit='', flimit=0, res=100, ampl=101, format='', normalize=1):
        "get data for frequency distribution graph"
        self.process_concordance_query()
        self.fcrit = fcrit
        conc = self.call_function(conclib.get_conc, (self._corp(),), asyn=0)
        if not conc.size():
            raise RuntimeError('Concordance is empty.')
        values = conclib.manatee.IntVector([0]*res)
        begs = conclib.manatee.IntVector([0]*res)
        conc.distribution(values, begs, ampl, normalize)
        begs2 = [j and conc.beg_at(i) or -1 for i, j in zip(begs, values)]
        ends = [0]*res
        i, j = 0, 1
        while j < res:
            if values[i]:
                if values[j]:
                    ends[i] = begs2[j]-1
                    j += 1
                    i = j-1
                else:
                    j += 1
            else:
                j += 1
                i += 1
        ends[i] = conc.end_at(conc.size()-1)
        return {
                'dots': [{
                    'frq': v[0],
                    'pos': i/float(len(values)),
                    'beg': int(v[1]),
                    'end': int(v[2]),
                    } for i, v in enumerate(zip(values, begs2, ends))],
                'granularity': res
        }

    def clear_cache (self, corpname=''):
        if not corpname: corpname = self.corpname
        if '..' in corpname or corpname.startswith('/'):
            return {'error': 'This action is not allowed.'}
        os.system ('rm -rf %s/%s' % (self._cache_dir, corpname))
        return {'message': 'Cache cleared: %s' % corpname}

    wlminfreq = 5
    wlmaxfreq = 0
    wlmaxitems = 100
    wlwords = []
    blacklist = []
    _wordlist_max_size = 0
    _keyword_max_size = 100

    def get_wl_words(self, attrnames=('wlfile', 'wlcache')):
            # gets arbitrary list of words for wordlist
        wlfile = getattr(self, attrnames[0], '')
        wlcache = getattr(self, attrnames[1], '')
        filename = wlcache; wlwords = []
        if wlfile: # save a cache file
            try:
                from hashlib import md5
            except ImportError:
                from md5 import new as md5
            filename = os.path.join(self._cache_dir,
                                    md5(wlfile.encode()).hexdigest() + '.wordlist')
            if not os.path.isdir(self._cache_dir): os.makedirs (self._cache_dir)
            cache_file = open(filename, 'w')
            cache_file.write(wlfile)
            cache_file.close()
            wlwords = [w.strip() for w in wlfile.splitlines()]
        if wlcache: # read from a cache file
            filename = os.path.join(self._cache_dir, wlcache)
            cache_file = open(filename)
            wlwords = [w.strip()
                       for w in cache_file.read().splitlines()]
            cache_file.close()
        return wlwords, os.path.basename(filename)


    include_nonwords = 0
    usengrams = 0
    ngrams_n = 2
    ngrams_max_n = 2
    nest_ngrams = 0
    wltype = 'simple'
    wlnums = 'frq'
    complement_subc = 0
    max_keywords = 100

    def check_wl_compatibility (self, wltype, ref_subcorp):
        if self.usengrams or ref_subcorp == '== the rest of the corpus ==':
            if wltype == 'multilevel':
                raise ConcError('N-grams are not compatible with changing '
                                  'output attribute(s)')
            if self.wlattr in ('WSCOLLOC', 'TERM') \
                     or '.' in self.wlattr:
                raise ConcError('N-grams and "rest of corpus" can use only '
                                  'positional attributes')
        if self.usengrams and ref_subcorp == '== the rest of the corpus ==':
            raise ConcError(_('N-grams and "rest of corpus" cannot be used'
                              'together'))
        if '.' in self.wlattr:
            if wltype != 'simple':
                raise ConcError('Text types are limited to simple output')
            if self.wlnums == 'arf':
                raise ConcError('ARF cannot be used with text types')
        if self.wlattr == 'WSCOLLOC' and self.wlsort != 'frq':
            raise ConcError('Word sketch collocations are available '
                            'with raw hit counts only')
        if self.wlattr == 'TERM' and self.wlsort != 'frq':
            raise ConcError('Terms are available with raw hit counts only')

    def wipo (self, single=0):
        from wipo_filters import filter_wipo_terms
        data = self.call_function(self.extract_keywords, (), attr='TERM',
               filter_singleword=not single, max_keywords=100000)
        if 'processing' in data: # bgjob in progress
            return data
        lang = self._corp().get_conf('LANGUAGE').split(', ')[0]
        keyterms = [x for x in filter_wipo_terms(data["keywords"], lang, single)]
        return { 'keywords': keyterms,
                 'single': single,
                 'lang': lang,
                 'size': len(keyterms),
               }


    def do_nest_ngrams(self, items, frqtype, itemkey='str'): # items must be sorted by freq
        from operator import itemgetter
        ngrams = [[], [], [], [], [], [], [], []]
             # (0-), (1-), 2-, 3-, 4-, 5-, 6-, (7-)grams
        for item in items:
            n = item[itemkey].count('\t') + 1
            item[itemkey] = '\t' + item[itemkey] + '\t'
            item['children'] = []
            item['nested'] = False
            for ng in reversed(ngrams[n+1]): # find superior n+1-gram
                if ng[frqtype] > item[frqtype]:
                    break
                if item[itemkey] in ng[itemkey]: # ng['freq'] == item['freq']
                    item['nested'] = True
                    ng['children'].append(item)
            for ng in ngrams[n-1]: # find subordinate (n-1)-grams
                if ng[itemkey] in item[itemkey]:
                    item['children'].append(ng)
                    ng['nested'] = True
            ngrams[n].append(item)
        result = ngrams[2]+ngrams[3]+ngrams[4]+ngrams[5]+ngrams[6]
        if self.wlsort == 'frq': result.sort(key=itemgetter(frqtype), reverse=True)
        else: result.sort(key=itemgetter(itemkey))
        for item in result:
            item[itemkey] = item[itemkey][1:-1]
        return result


    def wordlist (self, wlpat='.*', wltype='simple', corpname='', usesubcorp='',
                  ref_corpname='', ref_usesubcorp='', wlpage=1, relfreq=1, reldocf=1):
        sc = self._corp()
        regex_inline_flags = ""
        if self.wlicase and not self.wlattr.endswith("_lc") and self.wlattr != "lc":
            attrlist = sc.get_conf('ATTRLIST').split(',')
            if self.wlattr == "word" and "lc" in attrlist:
                self.wlattr = "lc"
            elif self.wlattr + '_lc' in attrlist:
                self.wlattr += '_lc'
            else:
                regex_inline_flags += "i"
        if self.wlusesubcorp: usesubcorp = self.usesubcorp = self.wlusesubcorp
        if wlpat and wlpat != '.*':
            m = re.match(r'(\(\?[a-zA-Z]\))?(.*)', wlpat)
            if m.group(1):
                regex_inline_flags += m.group(1)[1:-1]
            wlpat = '^%s$' % re.sub(' ', r'\\s+', m.group(2))
        self.check_wl_compatibility(wltype, ref_usesubcorp)
        result= { 'new_maxitems': self.wlmaxitems,
                  'wllimit': self._wordlist_max_size }
        wlstart = (wlpage - 1) * self.wlmaxitems
        self.wlmaxitems =  self.wlmaxitems * wlpage + 1 # +1 = end detection
        if self._wordlist_max_size and (self._wordlist_max_size < self.wlmaxitems):
            self.wlmaxitems = self._wordlist_max_size + 1
            result['lastpage'] = 1
            result['note'] = 'You are allowed to see only %s items.' \
                               % self._wordlist_max_size
        self.wlwords, self.wlcache = self.get_wl_words()
        self.blacklist, self.blcache = self.get_wl_words(('wlblacklist',
                                                                'blcache'))
        if self.include_nonwords:
            nwre = None
        else:
            nwre = sc.get_conf('NONWORDRE')
        if self.wlattr == 'WSCOLLOC':
            bgjob = self._ensure_fsa ((sc,), None, self.wlattr)
            if bgjob: return bgjob
            import wmap
            wmap.setEncoding(sc.get_conf('ENCODING'))
            ws = wmap.WMap (sc.get_conf('WSBASE'), sc)
            wl = ws.get_wordlist()
            if self.wlwords:
                self.wlwords = [s for s in self.wlwords if s.count("\t") == 2]
                if not self.wlwords:
                    return {"total": 0, "totalfrq": 0, "Items": []}
        elif self.wlattr == 'TERM': # NOT USED BY CRYSTAL NOW, JUST FOR DEBUGGING
            import wmap
            wmap.setEncoding(sc.get_conf('ENCODING'))
            bgjob = self._ensure_fsa ((sc, ), None, self.wlattr)
            if bgjob: return bgjob
            termbase = sc.get_conf('TERMBASE')
            if termbase.endswith("-ws"): # XXX
                termbase = termbase[:-3]
            wl = sc.get_wordlist(termbase)
            self.blacklist = [s.replace(" ", "_") + "-x" for s in self.blacklist]
            self.wlwords = [s.replace(" ", "_") + "-x" for s in self.wlwords]
        elif self.usengrams:
            bgjob = self._ensure_ngrams ((sc, ), self.wlattr)
            if bgjob: return bgjob
            self.wlattr += ".ngr"
            ngr = corplib.manatee.NGram(sc.get_conf('PATH') + self.wlattr,
                                        corplib.get_freqpath(sc, self.wlattr))
            bgjob = self._ensure_fsa ((sc, ), self.wlattr, 'NGRAM')
            if bgjob: return bgjob
            gram = "[^\t]+"
            ngr_re = "\t".join(self.ngrams_n * [gram])

            exclude_re = ''
            for blacklist_item in self.blacklist:
                if self.wlicase:
                    exclude_re += '(?i)(?!^.*\\b%s\\b.*$)(?-i)' % re.sub(' ', '\t', blacklist_item)
                else:
                    exclude_re += '(?!^.*\\b%s\\b.*$)' % re.sub(' ', '\t', blacklist_item)

            self.blacklist = []

            for i in range (self.ngrams_n, self.ngrams_max_n):
                ngr_re += "|" + "\t".join((i+1) * [gram])
            if wlpat and wlpat != '.*':
                wlpat = "(?=%s)%s(%s)" % (wlpat, exclude_re, ngr_re)
            else:
                wlpat = "%s(%s)" % (exclude_re, ngr_re)

            wl = ngr.get_wordlist()
            if nwre:
                nwre = "%s\t.*|.*\t%s\t.*|.*\t%s" % (nwre, nwre, nwre)
            if self.nest_ngrams:
                wlstart = 0
                self.wlmaxitems = max(self.wlmaxitems, self.wlpage*1000)
                if self._wordlist_max_size \
                      and self._wordlist_max_size < self.wlpage * 1000:
                    self.wlmaxitems = self._wordlist_max_size
                result['nested'] = self.nest_ngrams
        else: # plain attribute
            bgjob = self._ensure_fsa((sc, ), self.wlattr, 'ATTR')
            if bgjob: return bgjob
            if "." in self.wlattr:
                struc, strucattr = self.wlattr.split(".")
                struc = sc.get_struct (struc)
                wl = struc.get_attr (strucattr)
            else:
                wl = sc.get_attr (self.wlattr)
        if regex_inline_flags:
            wlpat = "(?%s)%s" % (regex_inline_flags, wlpat)
        try:
            sortfreq = wl.get_stat(self.wlsort)
        except corplib.manatee.FileAccessError:
            bgjob = corplib.compute_freqfile (self._user, sc, self.wlattr, self.wlsort, self.get_url())
            if bgjob: return bgjob_info(bgjob)
            sortfreq = wl.get_stat(self.wlsort)


        self.wlnums = self.wlnums and self.wlnums.split(",") or []
        self.wlnums = [f for f in self.wlnums if f != self.wlsort]
        addfreqs = []
        for f in self.wlnums:
            try:
                af = wl.get_stat(f)
            except corplib.manatee.FileAccessError:
                bgjob = corplib.compute_freqfile (self._user, sc, self.wlattr, f, self.get_url())
                if bgjob: return bgjob_info(bgjob)
                af = wl.get_stat(f)
            addfreqs.append(af)

        result_list, cnt, f = corplib.manatee.wordlist (wl, wlpat, addfreqs,
                              sortfreq, self.wlwords, self.blacklist, self.wlminfreq,
                              self.wlmaxfreq, self.wlmaxitems, nwre)

        def split_wlist_item (i):
            vals = i.split("\v")
            ret = {'str': vals[0]}
            for fi, f in enumerate([self.wlsort] + self.wlnums):
                freq = float(vals[fi + 1])
                if f in ["frq", "docf", "token:l", "norm:l"]:
                    freq = int(freq)
                ret[f] = freq
            return ret
        def split_triples (i):
            ret = split_wlist_item(i)
            parts = ret["str"].split("\t")
            ret["w1"], ret["gramrel"], ret["w2"] = parts[:3]
            if len(parts) > 3:
                ret["cm"] = parts[3]
            return ret

        if self.wlattr == 'WSCOLLOC':
            result_list = list(map(split_triples, result_list))
        else:
            result_list = list(map(split_wlist_item, result_list))

        if relfreq and (self.wlsort == 'frq' or 'frq' in self.wlnums):
            size = sc.search_size()
            for item in result_list:
                if self.usengrams:
                    item['relfreq'] = round(item['frq'] * 1000000 / min([size, 1000000000]), 5)  # TODO - hack, because of 1 bilion restriction, fix when item['frq'] is computed for whole corpus
                else:
                    item['relfreq'] = round(item['frq'] * 1000000 / size, 5)
        if reldocf and (self.wlsort == 'docf' or 'docf' in self.wlnums):
            size = sc.get_struct(sc.get_conf("DOCSTRUCTURE")).search_size()
            for item in result_list:
                item['reldocf'] = round(item['docf'] * 100 / (size if size >= 1 else 1), 5)
        result['total'] = cnt
        result['totalfrq'] = f
        if self.wlwords: result['wlcache'] = self.wlcache
        if self.blacklist: result['blcache'] = self.blcache
        if self.nest_ngrams:
            result_list = self.do_nest_ngrams(result_list, self.wlsort)
        if len(result_list) < self.wlmaxitems: result['lastpage'] = 1
        else: result['lastpage'] = 0; result_list = result_list[:-1]
        result_list = result_list[wlstart:]
        result['Items'] = result_list
        self.wlmaxitems -= 1
        try:
            if not self.wlattr in ('TERM', 'WSCOLLOC'):
                result['wlattr_label'] = sc.get_conf(
                                       self.wlattr+'.LABEL') or self.wlattr
        except:
            result['wlattr_label'] = self.wlattr
        result['frtp'] = corplib.get_stat_desc (self.wlsort)
        return result

    wlstruct_attr1 = ''
    wlstruct_attr2 = ''
    wlstruct_attr3 = ''

    def make_wl_query(self, random=0):
        qparts = []
        if self.wlpat: qparts.append('%s="%s"' % (self.wlattr, self.wlpat))
        if not self.include_nonwords:
            qparts.append('%s!="%s"' % (self.wlattr,
                                        self._corp().get_conf('NONWORDRE')))
        if self.wlwords:
            qq = ['%s=="%s"' % (self.wlattr, w.strip()) for w in self.wlwords]
            qparts.append('(' + '|'.join(qq) + ')')
        for w in self.blacklist:
            qparts.append('%s!=="%s"' % (self.wlattr, w.strip()))
        if random: prefix = 'R'
        else: prefix = ''
        self.q = [prefix + 'q[' + '&'.join(qparts) + ']']

    def struct_wordlist (self, random=0):
        if self.wlusesubcorp: usesubcorp = self.usesubcorp = self.wlusesubcorp
        if self.fcrit:
            self.wlwords, self.wlcache = self.get_wl_words()
            self.blacklist, self.blcache = self.get_wl_words(('wlblacklist',
                                                                    'blcache'))
            self.make_wl_query(random)
            return self.freqs (self.fcrit, self.flimit, self.freq_sort, 1)

        if '.' in self.wlattr:
            raise ConcError('Text types are limited to Simple output')
        if self.wlnums != 'frq':
            raise ConcError('Multilevel lists are limited to Word counts frequencies')
        if self.wlattr == 'WSCOLLOC':
            raise ConcError('Word sketch collocations are not compatible ' +\
                            'with Multilevel wordlist')
        level = 3
        self.wlwords, self.wlcache = self.get_wl_words()
        self.blacklist, self.blcache = self.get_wl_words(('wlblacklist',
                                                                    'blcache'))
        if not self.wlstruct_attr1:
            raise ConcError('No output attribute specified')
        if not self.wlstruct_attr3: level = 2
        if not self.wlstruct_attr2: level = 1
        if not self.wlpat and not self.wlwords:
            raise ConcError('You must specify either a regular expression or a file to get the multilevel wordlist')
        self.make_wl_query(random)
        self.flimit = self.wlminfreq
        self.fmaxitems = self.wlmaxitems
        return  self.freqml (flimit=self.wlminfreq, freqlevel=level,
                ml1attr=self.wlstruct_attr1, ml2attr=self.wlstruct_attr2,
                ml3attr=self.wlstruct_attr3)

    subcnorm = 'freq'

    def texttypes_with_norms(self, subcorpattrs='', list_all=False, ret_nums=True):
        corp = self._corp()
        if not os.path.exists(os.path.join(corp.get_conf('PATH'), 'sizes')):
            # corpus not compiled
            return {'Normlist': [], 'Blocks': []}
        if not subcorpattrs:
            subcorpattrs = corp.get_conf ('SUBCORPATTRS') \
                               or corp.get_conf ('FULLREF')
        if not subcorpattrs or subcorpattrs == '#':
            return {'Normslist': [], 'Blocks': []}
        tt = corplib.texttype_values(corp, subcorpattrs, list_all, self.hidenone)
        if not ret_nums: return {'Blocks': tt, 'Normslist': []}
        basestructname = subcorpattrs.split('.')[0]
        struct = corp.get_struct (basestructname)
        normvals = {}
        if self.subcnorm not in ('freq', 'tokens'):
            try:
                nas = struct.get_attr (self.subcnorm).pos2str
            except conclib.manatee.AttrNotFound as e:
                self.error = str(e)
                self.subcnorm = 'freq'
        # TODO: do we need norms here in Bonito4?
        for item in tt:
            for col in item['Line']:
                if 'textboxlength' in col: continue
                if not col['name'].startswith(basestructname + '.'): # new structure
                    basestructname = col['name'].split('.')[0]
                    struct = corp.get_struct (basestructname)
                    normvals = {}
                    if self.subcnorm not in ('freq', 'tokens'):
                        try:
                            nas = struct.get_attr (self.subcnorm).pos2str
                        except conclib.manatee.AttrNotFound as e:
                            self.error = str(e)
                            self.subcnorm = 'freq'
                attr = struct.get_attr(col['name'].split('.')[-1])
                p2i = attr.pos2id
                xcnt_dict = dict([(i, 0) for i in range(attr.id_range())])
                if self.subcnorm == 'freq':
                    for vid in range(attr.id_range()):
                        xcnt_dict[vid] = attr.freq(vid)
                elif self.subcnorm == 'tokens':
                    for sid in range(struct.size()):
                        vid = p2i(sid)
                        xcnt_dict[vid] += struct.end(sid) - struct.beg(sid)
                else:
                    for vid in range(attr.id_range()):
                        xcnt_dict[vid] = attr.norm(vid)
                if not col.get('hierarchical', ''):
                    for val in col['Values']:
                        val['xcnt'] = xcnt_dict.get(attr.str2id(str(val['v'])), 0)
        return {'Blocks': tt, 'Normslist': self.get_normslist(basestructname)}

    def get_normslist(self, structname):
        corp = self._corp()
        normsliststr = corp.get_conf ('DOCNORMS')
        normslist = [{'n':'freq', 'label': 'Document counts'},
                     {'n':'tokens', 'label': 'Tokens'}]
        if normsliststr:
            normslist += [{'n': n, 'label': corp.get_conf (structname + '.'
                                                          + n + '.LABEL') or n}
                          for n in normsliststr.split(',')]
        else:
            try:
                corp.get_attr(structname + ".wordcount")
                normslist.append({'n':'wordcount', 'label': 'Word counts'})
            except:
                pass
        return normslist

    def _texttype_query (self):
        scas = [(a[4:], getattr (self, a))
                for a in dir(self) if a.startswith ('sca_')]
        fscas = [(a[5:], getattr (self, a))
                 for a in dir(self) if a.startswith ('fsca_')]
        structs = {}
        for sa, v in scas: # checkbox input
            if '.' in sa:
                s, a = sa.split('.')
                if type(v) is type([]):
                    query = '(%s)' % ' | '.join (['%s="%s"' % (a,escape(v1))
                                                  for v1 in v])
                else:
                    query = '%s="%s"' % (a,escape(v))
            else: # structure number
                s = sa
                if type(v) is type([]):
                    query = '(%s)' % ' | '.join (['#%s' % x.split('#')[1] for x in v])
                else:
                    query = '#%s' % v.split('#')[1]
            if s not in structs: structs[s] = []
            structs[s].append (query)
        for sa, v in fscas: # free text input (allows REs)
            s, a = sa.split('.')
            query = '%s="%s"' % (a, v)
            if s not in structs: structs[s] = []
            structs[s].append (query)
        return tuple([(sname, ' & '.join(subquery)) for
                sname, subquery in list(structs.items())])

    def subcorp (self, subcname='', delete='', create=False, q='', struct='', ttq='',
                 create_subcorp_under='', instantSubCorp=''):
        if delete:
            base = os.path.join (self.subcpath[-1], self.corpname,
                                 self.urlencode(subcname))
            for e in glob.glob(base + '.*'):
                if os.path.isfile(e):
                    os.unlink(e)
        tt_query = ttq or self._texttype_query()
        if create and not subcname:
            raise ConcError ('No subcorpus name specified!')
        if (not subcname or (not tt_query and delete)
            or (not delete and not create)):
            subcList = self.cm.subcorp_names (self.corpname)
            if subcList and not subcname:
                subcname = subcList[0]['n']
            return {'subcname': subcname,
                    'SubcorpList': self.cm.subcorp_names (self.corpname)}
        if self._anonymous:
            return {'error': 'Anonymous users are not allowed to create subcorpora.'}
        basecorpname = create_subcorp_under or self.corpname.split(':')[0]
        path = os.path.join (self.subcpath[-1], basecorpname)
        if not os.path.isdir (path):
            os.makedirs (path)
        path = os.path.join (path, self.urlencode(subcname)) + '.subc'
        if self._curr_corpus is None:
            self._corp()
        # XXX ignoring more structures
        if q:
            if create_subcorp_under:
                self.q.append('x-%s' % create_subcorp_under.split('/')[-1])
            conc = self.call_function (conclib.get_conc,
                    (self._curr_corpus, self.samplesize), asyn=0)
            s = self._curr_corpus.get_struct(struct)
            cs = conclib.manatee.create_subcorpus (path, conc.RS(), s)
            if cs:
                corplib.save_subcdef(path, subcname,
                                struct or '--NONE--', 'Q:' + '\v'.join(self.q))
                return {'subcorp': subcname, 'message': "Subcorpus saved."}
            else:
                return {'error': "Nothing saved: empty subcorpus!"}
        else:
            if not tt_query:
                raise ConcError('Nothing specified!')
            structname, subquery = tt_query[0]
            if conclib.manatee.create_subcorpus(path, self._curr_corpus,
                    structname, subquery):
                subcdeff = None
                if instantSubCorp:
                    existing_path = self.cm.find_same_subcorp_file(basecorpname, path, "###INSTANT###", None, None, self.urlencode("###") + "*" + self.urlencode("###"))
                    if existing_path:
                        from urllib.parse import unquote_plus
                        subcname = unquote_plus(os.path.splitext(os.path.basename(existing_path))[0])
                        subcdeff = existing_path + "def"
                        os.unlink(path)
                if not subcdeff: # save subc def file if necessary
                    subcdeff = path + "def"
                    if not os.path.isfile(subcdeff):
                        subcdeff = corplib.save_subcdef(path,
                                subcname, structname, subquery)
                finalname = '%s:%s' % (basecorpname, subcname)
                sc = self.cm.get_Corpus (finalname)
                return {'subcorp': finalname,
                        'subcorp_deffile': subcdeff,
                        'corpsize': sc.size(),
                        'subcsize': sc.search_size(),
                        'SubcorpList': self.cm.subcorp_names (self.corpname)}
            else:
                raise ConcError('Empty subcorpus!')

    def subcorp_info (self, subcname=''):
        sc = self.cm.get_Corpus (self.corpname, subcname)
        return {'subcorp': subcname,
                'corpsize': sc.size(),
                'subcsize': sc.search_size()}

    def rebuild_subc(self, subcname=''):
        import urllib.request, urllib.parse, urllib.error
        qsubcname = urllib.parse.quote_plus(subcname)
        subcp = os.path.join(self.subcpath[-1], self.corpname,
                qsubcname + '.subcdef')
        subcn, subcs, subcq = corplib.parse_subcdef(subcname, subcp)
        for e in glob.glob(subcp.replace('.subcdef', '.*')):
            if os.path.isfile(e) and not e.endswith('.subcdef'):
                os.unlink(e)
        if all([subcn, subcs, subcq]):
            subcs = subcs.replace('--NONE--', '')
            self._curr_corpus.spath = subcp[:-3]
            if subcq.startswith('Q:'):
                self.q = subcq[2:].split('\v')
                return self.subcorp(subcname, False, True, subcq[2:], subcs, '')
            else:
                return self.subcorp(subcname, False, True, '', '', [(subcs, subcq)])
        else:
            raise RuntimeError('Failed to rebuild subcorpus')

    def corp_info(self, gramrels=0, corpcheck=0, registry=0, subcorpora=0,
            struct_attr_stats=0):
        out = corplib.get_corp_info(self._corp(), registry, gramrels,
                corpcheck, struct_attr_stats)
        compiled = int(out['sizes'].get('tokencount', 0)) > 1
        if compiled and subcorpora:
            tokens = out['sizes']['tokencount']
            words = out['sizes'].get('wordcount', tokens)
            wtr = int(words) / float(tokens)
            subcorp_id2name = self.get_user_options(options=['subcorp_id2name'], corpus=self.corpname)['user'].get('subcorp_id2name', {})
            scs = self.cm.subcorp_names(self.corpname, subcorp_id2name)
            for sc in scs:
                sub = self.cm.get_Corpus(self.corpname, sc['n'])
                subc_size = sub.search_size()
                sc['tokens'] = subc_size
                sc['relsize'] = subc_size / float(tokens) * 100
                sc['words'] = int(subc_size * wtr)
                sc['struct'] = hasattr(sub, 'subcdef') and sub.subcdef[1] or ""
                sc['query'] = hasattr(sub, 'subcdef') and sub.subcdef[2] or ""
            out['subcorpora'] = scs
        else:
            out['subcorpora'] = []
        return out

    def subcorp_rename(self, subcorp_id='', new_subcorp_name=''):
        current_names = self.get_user_options(options=['subcorp_id2name'], corpus=self.corpname)['user'].get('subcorp_id2name', {})
        current_names[subcorp_id] = new_subcorp_name
        self.set_user_options(options={'subcorp_id2name': current_names}, corpus=self.corpname)
        return {'status': 'OK', 'corpus': self.corpname, 'subcorp_id2name': current_names}

    def attr_vals(self, avattr='', avpat='.*', avmaxitems=20, avfrom=0, icase=1):
        if not avattr:
            return {'error': 'Parameter avattr is required'}
        return corplib.attr_vals(self.abs_corpname(self.corpname), avattr,
                avpat, avmaxitems, avfrom, icase)

    def annot_download(self):
        "get list of all queries and labels"
        # TODO: download also annotated concordances
        return Annotation(self._corp(), self.annotation_group, self._user).download()

    def annot_onto(self):
        "get ontology hierarchy"
        return Annotation(self._corp(), self.annotation_group, self._user).ontology()

    def annot_list_path(self):
        "list values at some position in JSON data"
        # TODO: use annotlib.listing
        raise NotImplementedError

    def annot_query_labels(self, semtype=[], position=[]):
        "query JSON data in labels"
        return Annotation(self._corp(), self.annotation_group, self._user).browse_labels(semtype, position)

    def annot_rename_labels(self, qid=-1, data=""):
        "rename labels in batch"
        a = Annotation(self._corp(), self.annotation_group, self._user)
        return a.rename_labels(qid, data)

    def annot_save_query(self, id=-1, status=""):
        "save query"
        a = Annotation(self._corp(), self.annotation_group, self._user)
        # we can save potentially any JSON to a query (column attr)
        return a.save_query(id, status)

    def annot_save_label(self, qid=-1, lid=-1, data='{}', attr='{}'):
        "save JSON data and JSON attr for query qid and label lid"
        a = Annotation(self._corp(), self.annotation_group, self._user)
        return a.save_label(qid, lid, data, attr)

    def _storeconc_path(self):
        "get absolute path to conc file without suffix"
        return os.path.join(self._corp()._conc_dir, self.annotconc)

    def get_stored_conc(self):
        "load stored concordance with annotations"
        conc = conclib.manatee.Concordance(self._corp(), self._storeconc_path() + '.conc')
        a = Annotation(self._corp(), self.annotation_group, self._user)
        conc.labelmap = a.get_labelmap(self.annotconc)
        return conc

    def storeconc (self, storeconcname=''):
        "save concordance into .conc file for later annotation"
        if self.concordance_query: self.process_concordance_query()
        conc = self.call_function(conclib.get_conc, (self._corp(),), asyn=0)
        self.annotconc = storeconcname
        cpath = self._storeconc_path()
        cdir = os.path.dirname(cpath)
        if os.path.exists(cpath + '.conc'):
            return {'stored': storeconcname, 'new': False}
        if not os.path.isdir(cdir):
            os.makedirs(cdir)
        conc.save(cpath + '.conc')
        if self.q[0].startswith('a'):
            self.q[0] = self.q[0].split(',', 1)[1]
        qq = ';'.join(self.q)
        rq = [qi[1:] for qi in self.q if qi.startswith('r')]
        ss = rq and int(rq[0]) or 0
        a = Annotation(self._corp(), self.annotation_group, self._user)
        resp = a.store_query(concname=storeconcname, queryname=storeconcname,
                query=qq, size=conc.size(), sample=ss)
        return {'stored': storeconcname, 'resp': resp, 'new': True}

    def purge_annotations(self): # for testing purposes
        "remove all stored concordances and the SQLite DB for the corpus"
        from shutil import rmtree
        try:
            rmtree(self._corp()._conc_dir)
            return {'message': 'All annotations have been deleted'}
        except OSError as e:
            return {'message': 'Failed to delete annotations'}

    def delstored(self, annotconc=''):
        cpath = self._storeconc_path()
        a = Annotation(self._corp(), self.annotation_group, self._user)
        do = a.del_conc(annotconc)
        try:
            os.unlink(cpath + '.conc')
        except OSError:
            pass
        # remove also from cache
        from conccache import del_from_map
        subchash = getattr(self._corp(), 'subchash', None)
        cache_dir = self._cache_dir + '/' + self.corpname + '/'
        del_from_map(cache_dir, subchash, ('s' + annotconc,))
        o = {}
        o['message'] = 'Successfully removed'
        o['skema'] = do.get('message', 'Query removed from DB')
        o['removed'] = annotconc
        return o

    def _selectstored (self, annotconc):
        if os.path.exists (self._storeconc_path() + '.conc'):
            return True
        return False

    def storedconcs(self):
        a = Annotation(self._corp(), self.annotation_group, self._user)
        return a.queries()

    def addlngroup(self, label=""):
        if not label:
            return {'error': 'Missing label'}
        a = Annotation(self._corp(), self.annotation_group, self._user)
        return a.add_label_for_query(self.annotconc, label)

    def renlngroup(self, qid=-1, lid=-1, label=""):
        "Rename label"
        if -1 in [lid, qid] or not label:
            return {'error': 'Missing label or query'}
        a = Annotation(self._corp(), self.annotation_group, self._user)
        return a.rename_label(qid, lid, label)

    def dellngroup(self, lid=-1, qid=-1):
        if lid == -1 or qid == -1:
            return {'error': 'Missing label or query'}
        a = Annotation(self._corp(), self.annotation_group, self._user)
        return a.del_label(qid, lid)

    def setlngroup(self, toknum='', group=0):
        conc = self.get_stored_conc()
        l = 0
        for tn in set(toknum.strip().split()):
            conc.set_linegroup_at_pos(int(tn), group)
            l += 1
        conc.save (self._storeconc_path() + '.conc', 1)
        lab = conc.labelmap.get (group, group)
        return {'label': lab, 'count': l}

    def setlngroupglobally (self, group=0):
        annot = self.get_stored_conc()
        conc = self.call_function (conclib.get_conc, (self._corp(),))
        conc.set_linegroup_from_conc (annot)
        conc.set_linegroup_globally (group)
        annot.set_linegroup_from_conc (conc)
        annot.save (self._storeconc_path() + '.conc', 1)
        lab = annot.labelmap.get (group, group)
        return {'label': lab, 'count': conc.size()}

    def lngroupinfo(self, annotconc=''):
        a = Annotation(self._corp(), self.annotation_group, self._user)
        conc = None if a.conn is None else self.get_stored_conc()
        return a.labels(conc, query=annotconc)

    minbootscore=0.5
    minbootdiff=0.8
    def bootstrap (self, annotconc='', minbootscore=0.5, minbootdiff=0.8):
        import wsclust
        annot = self.get_stored_conc()
        ws = self.call_function (wsclust.WSCluster, ())
        ws.build_pos2coll_map()
        log = ws.bootstrap_conc (annot, minbootscore, minbootdiff)
        annot.save (self._storeconc_path() + '.conc', 1)
        del annot
        self.q = ['s' + annotconc]
        out = self.lngroupinfo (annotconc)
        out['auto_annotated'] = len(log)
        return out


    def fcs(self, operation='explain', version='', recordPacking='xml',
            extraRequestData='', query='', startRecord='', responsePosition='',
            recordSchema='', maximumRecords='', scanClause='', maximumTerms='',
            stylesheet=''):
        "Federated content search API function (www.clarin.eu/fcs)"

        # default values
        self._headers['Content-Type'] = 'application/xml'
        numberOfRecords = 0
        current_version = 1.2
        maximumRecords_ = 250
        maximumTerms_ = 100
        startRecord_ = 1
        responsePosition_ = 0
        # supported parameters for all operations
        sup_pars = ['operation', 'stylesheet', 'version', 'extraRequestData', 'format']
        try:
            mc = manatee.Corpus(self.abs_corpname(self.corpname))
            pretty_corp_name = mc.get_conf('NAME') 
        except:
            pretty_corp_name = self.corpname

        out = {'operation': operation, 'version': current_version,
               'recordPacking': recordPacking, 'result': [],
               'error': False, 'numberOfRecords': numberOfRecords,
               'server_name': self.environ.get('SERVER_NAME', ''),
               'server_port': self.environ.get('SERVER_PORT', '80'),
               'database': self.environ.get('SCRIPT_NAME', '')[1:] + '/fcs',
               'xml_stylesheet': stylesheet, 
               'pretty_corpname': pretty_corp_name,
               'corpname': self.corpname,
               }
        fcs_err = None
        try:
            # check version
            if version and current_version < float(version):
                fcs_err = Exception(5, version, 'Unsupported version')

            # check integer parameters
            if maximumRecords != '':
                try:
                    maximumRecords_ = int(maximumRecords)
                except:
                    fcs_err = Exception(6, 'maximumRecords',
                                        'Unsupported parameter value')
                if maximumRecords_ < 0:
                    fcs_err = Exception(6, 'maximumRecords',
                                        'Unsupported parameter value')

            out['maximumRecords'] = maximumRecords_
            if maximumTerms != '':
                try:
                    maximumTerms_ = int(maximumTerms)
                except:
                    fcs_err = Exception(6, 'maximumTerms',
                                        'Unsupported parameter value')
            out['maximumTerms'] = maximumTerms_
            if startRecord != '':
                try:
                    startRecord_ = int(startRecord)
                except:
                    fcs_err = Exception(6, 'startRecord',
                                        'Unsupported parameter value')
                if startRecord_ <= 0:
                    fcs_err = Exception(6, 'startRecord',
                                        'Unsupported parameter value')
            out['startRecord'] = startRecord_
            if responsePosition != '':
                try:
                    responsePosition_ = int(responsePosition)
                except:
                    fcs_err = Exception(6, 'responsePosition',
                                        'Unsupported parameter value')
            out['responsePosition'] = responsePosition_

            # set content-type in HTTP header
            if recordPacking == 'string':
                self._headers['Content-Type'] = 'text/plain'
            elif recordPacking == 'xml':
                self._headers['Content-Type'] = 'application/xml'
            else:
                fcs_err = Exception(71, 'recordPacking',
                                    'Unsupported record packing')

            # provide info about service
            if operation == 'explain' or not operation:
                sup_pars.append('recordPacking') # other supported parameters
                unsup_pars = list(set(self._url_parameters) - set(sup_pars))
                if unsup_pars:
                    raise Exception(8, unsup_pars[0], 'Unsupported parameter')
                #if extraRequestData:
                #    corpname = extraRequestData
                corp = self._corp()
                out['result'] = corp.get_conf('ATTRLIST').split(',')
                out['numberOfRecords'] = len(out['result'])

            # wordlist for a given attribute
            elif operation == 'scan':
                # special handling of fcs.resource = root
                if scanClause.startswith('fcs.resource'):
                    out['operation'] = 'fcs.resource'
                    out['resource_info'] = False
                    copts = []
                    if (hasattr(self, 'x-cmd-resource-info')
                        and getattr(self, 'x-cmd-resource-info') == 'true'):
                        copts = ['DESCRIPTION', 'INFOHREF', 'LANGUAGE']
                        out['resource_info'] = True
                    corps = self.cm.corplist_with_names(copts)
                    out['FCSCorpora'] = corps[:maximumTerms_]
                else:
                    # check supported parameters
                    sup_pars.extend(['scanClause', 'responsePosition',
                                     'maximumTerms'])
                    unsup_pars = list(set(self._url_parameters) - set(sup_pars))
                    if unsup_pars:
                        raise Exception(8, unsup_pars[0], 'Unsupported parameter')
                    #if extraRequestData:
                    #    corpname = extraRequestData
                    out['result'] = conclib.fcs_scan(
                        self.abs_corpname(self.corpname), scanClause,
                        maximumTerms_, responsePosition_)

            # simple concordancer
            elif operation == 'searchRetrieve':
                # check supported parameters
                sup_pars.extend(['query', 'startRecord', 'maximumRecords',
                        'recordPacking', 'recordSchema', 'resultSetTTL',
                                 'x-cmd-context'])
                unsup_pars = list(set(self._url_parameters) - set(sup_pars))
                if unsup_pars:
                    raise Exception(8, unsup_pars[0], 'Unsupported parameter')
                if hasattr(self, 'x-cmd-context'):
                    corpname = getattr(self, 'x-cmd-context')
                    if corpname in self.corplist:
                        self._curr_corpus = None
                        self.corpname = corpname
                out['result'] = conclib.fcs_search(self._corp(), query,
                        maximumRecords_, startRecord_ -1)
                out['numberOfRecords'] = len(out['result'])

            # unsupported operation
            else:
                out['operation'] = 'explain' # show within explain template
                raise Exception(4, 'operation', 'Unsupported operation')
            if fcs_err:
                out['error'] = True
                out['code'], out['details'], out['msg'] = (
                    fcs_err[0], fcs_err[1], fcs_err[2])
            return out

        # catch exception and amend diagnostics in template
        except Exception as e:
            out['error'] = True
            try: # concrete error, catch message from lower levels
                out['code'], out['details'], out['msg'] = e[0], e[1], e[2]
            except: # general error
                out['code'], out['details'] = 1, repr(e)
                out['msg'] = 'General system error'
            return out

    def extract_keywords(self, ref_corpname='', simple_n=1.0, reldocf=1,
            attr='lc', alnum=0, onealpha=1, ref_usesubcorp='', icase=0,
            minfreq=5, maxfreq=0, max_keywords=100, lang_code='en', wlpat='.*',
            include_nonwords=0, usengrams=0, addfreqs='', filter_singleword=True, examples_no=0):

        note = ''
        if max_keywords > self._keyword_max_size:
            note = f'You requested {max_keywords} items but you are allowed to see only {self._keyword_max_size} items.'
            max_keywords = self._keyword_max_size

        self.wlwords, self.wlcache = self.get_wl_words()
        self.blacklist, self.blcache = self.get_wl_words(('wlblacklist', 'blcache'))
        if minfreq == "auto": # XXX see wsketchcgi :-(
            minfreq = 5
        if not ref_corpname:
            return {'error': "Reference corpus required"}

        nwre = "" if include_nonwords else self._corp().get_conf("NONWORDRE")
        neg_filters = []

        if usengrams:
            ngr_re = "\t".join(self.ngrams_n * ["[^\t]+"])
            for i in range (self.ngrams_n, self.ngrams_max_n):
                ngr_re += "|" + "\t".join((i+1) * ["[^\t]+"])
            filters = ["(?=^%s$)(%s)" % (wlpat, ngr_re)]
            if nwre:
                neg_filters = ["%s\t.*|.*\t%s\t.*|.*\t%s" % (nwre, nwre, nwre)]
        else:
            filters = [wlpat]

            # old terms temporary fix
            if attr == "TERM" and self._corp().get_conf('TERMDEF').endswith('.wsdef.m4'):
                new_wlpat = wlpat.replace(" ", "_")
                filters = [new_wlpat]
                if self._corp().get_conf('WSSTRIP') == 2:
                    filters = [f'{new_wlpat}-x']
                    
            if nwre:
                neg_filters = [nwre]

        addfreqs = addfreqs and addfreqs.split(",") or []
        if alnum:
            if attr == "TERM":
                filters.append(r"^[\w_\- ]+$")
            else:
                filters.append(r"^[\w\-\t ]+$")
        if onealpha:
            filters.append(r"^.*(?![\d])\w.*$")
        if attr == "TERM" and filter_singleword:
            filters.append(r"^.*[ _].*$")
        if icase and not attr.endswith("_lc") and attr != "lc":
            attrlist = self._corp().get_conf('ATTRLIST').split(',')
            if attr == "word" and "lc" in attrlist:
                attr = "lc"
            elif attr + '_lc' in attrlist:
                attr += '_lc'
            else:
                filters = ["(?i)" + f for f in filters]
        c = self._corp() # both must have the same encoding
        if ref_usesubcorp == '== the rest of the corpus ==':
            rc = self.cm.get_Corpus (ref_corpname, self.usesubcorp,
                                     complement=True)
        else:
            rc = self.cm.get_Corpus(ref_corpname, ref_usesubcorp)
        if attr == "TERM":
            import wmap
            bgjob = self._ensure_fsa ((c, rc), None, attr)
            if bgjob: return bgjob
            c_tb = c.get_conf("TERMBASE")
            if c_tb.endswith("-ws"): # XXX
                c_tb = c_tb[:-3]
            c_wl = c.get_wordlist(c_tb)
            rc_tb = rc.get_conf("TERMBASE")
            if rc_tb.endswith("-ws"): # XXX
                rc_tb = rc_tb[:-3]
            rc_wl = rc.get_wordlist(rc_tb)
        elif attr == "WSCOLLOC":
            import wmap
            c_ws = wmap.WMap(c.get_conf("WSBASE"), c)
            rc_ws = wmap.WMap(rc.get_conf("WSBASE"), rc)
            bgjob = self._ensure_fsa ((c, rc), None, attr)
            if bgjob: return bgjob
            c_wl = c_ws.get_wordlist()
            rc_wl = rc_ws.get_wordlist()
        elif usengrams:
            bgjob = self._ensure_ngrams ((c, rc), attr)
            if bgjob: return bgjob
            c_freqpath = rc_freqpath = ''
            attr += ".ngr"
            if hasattr(c, 'spath'):
                c_freqpath = c.spath[:-4] + attr
            if hasattr(rc, 'spath'):
                rc_freqpath = rc.spath[:-4] + attr
            c_ngr = corplib.manatee.NGram(c.get_conf("PATH") + attr, c_freqpath)
            rc_ngr = corplib.manatee.NGram(rc.get_conf("PATH") + attr, rc_freqpath)
            bgjob = self._ensure_fsa ((c, rc), attr, 'NGRAM')
            if bgjob: return bgjob
            c_wl = c_ngr.get_wordlist()
            rc_wl = rc_ngr.get_wordlist()
        else:
            bgjob = self._ensure_fsa((c, rc), attr, 'ATTR')
            if bgjob: return bgjob
            c_wl = c.get_attr(attr)
            rc_wl = rc.get_attr(attr)

        # difference from plain wordlist: the required frequency does not need to be present in both corpora (focus and reference)
        # so we allow missing frequencies which we cannot calculate (e.g. star without STARATTR or docf without DOCSTRUCTURE)
        for cc, ww in [(c, c_wl), (rc, rc_wl)]:
            for freqtype in addfreqs + ["frq"]:
                try:
                    _f = ww.get_stat(freqtype)
                except corplib.manatee.FileAccessError:
                    notavail = False
                    if freqtype.startswith("star:"):
                        try:
                            _a = cc.get_attr(cc.get_conf("DOCSTRUCTURE") + "." + cc.get_conf("STARATTR"))
                        except conclib.manatee.AttrNotFound:
                            notavail = True
                    elif freqtype == "docf":
                        try:
                            _a = cc.get_struct(cc.get_conf("DOCSTRUCTURE"))
                        except conclib.manatee.AttrNotFound:
                            notavail = True
                    if not notavail:
                        bgjob = corplib.compute_freqfile (self._user, cc, attr, freqtype, self.get_url())
                        if bgjob: return bgjob_info(bgjob)
        keyword = corplib.manatee.Keyword(c, rc, c_wl, rc_wl, simple_n, max_keywords,
                                          minfreq, maxfreq, self.blacklist, self.wlwords, 'frq', addfreqs,
                                          filters, neg_filters, None)

        result_list = []
        kw = keyword.next()
        while kw:
            s = kw.str
            item = {}
            if attr == "TERM":
                cql = '[term("%s")]' % escape(s)
                s = s.replace("_", " ") # XXX remove in data
                if s.endswith("-x"): # XXX remove in data
                    s = s[:-2]
            elif attr == "WSCOLLOC":
                parts = s.split("\t")
                item["w1"], item["gramrel"], item["w2"] = parts[:3]
                if len(parts) > 3:
                    item["cm"] = parts[3]
                cql = '[ws("%s","%s","%s")]' % (escape(item["w1"]), escape(item["gramrel"]), escape(item["w2"]))
            elif usengrams:
                ngr = s.split("\t")
                cql = "".join(['[%s="%s"]' % (attr[:-4], escape(x)) for x in ngr])
            else:
                cql = '[%s="%s"]' % (attr, escape(s))
            freqs = kw.get_freqs(2*len(addfreqs) + 4)
            item.update({'item': s,
                    'score': round(kw.score, 3),
                    'frq1': int(freqs[0]),
                    'frq2': int(freqs[1]),
                    'rel_frq1': round(float(freqs[2]), 5),
                    'rel_frq2': round(float(freqs[3]), 5),
                    'query': cql})
            for fi, f in enumerate(addfreqs):
                f = f.split(":")[0]
                item[f + "1"] = freqs[2*fi+4]
                item[f + "2"] = freqs[2*fi+5]
            result_list.append(item)

            if int(examples_no) > 0:
                gdex_exmaples = get_n_gdex_examples(cql, self._corp(), ref_corpname.strip().split('/')[-1], int(examples_no))
                item.update({'gdex_examples': gdex_exmaples})

            kw = keyword.next()

        if reldocf and 'docf' in addfreqs:
            size1 = c.get_struct(c.get_conf("DOCSTRUCTURE")).search_size()
            size2 = rc.get_struct(rc.get_conf("DOCSTRUCTURE")).search_size()
            for item in result_list:
                item['rel_docf1'] = round(item['docf1'] * 100 / size1, 5)
                item['rel_docf2'] = round(item['docf2'] * 100 / size2, 5)
        if usengrams and self.nest_ngrams:
            result_list = self.do_nest_ngrams(result_list, 'frq1', 'item')
        total, totalfrq1, totalfrq2 = keyword.get_totals()


        return {'keywords': result_list,
                'reference_corpus_name': rc.get_conf('NAME'),
                'reference_corpus_size': rc.size(),
                'reference_subcorpus_size': rc.search_size(),
                'subcorpus_size': c.search_size(),
                'corpus_size': c.size(),
                'total': total,
                'totalfrq1': totalfrq1,
                'totalfrq2': totalfrq2,
                'wllimit': max_keywords,
                'note': note}

    def translate_words(self, l2_corpname='', data=''):
        return conclib.translate_words(self._corp(),
                self.abs_corpname(l2_corpname), data)

    def translate_kwic(self, bim_corpname='', data=''):
        result = conclib.translate_kwic(self._corp(),
                                        self.abs_corpname(bim_corpname), data)
        return {'toknum2words': result[1], 'dict': result[0], 'corpus': bim_corpname}

    def bidict(self, l2_corpname=''):
        if self.corpname.startswith('preloaded/'):
            return {'error': 'Not available for preloaded corpora'}
        from translate import Translator
        try:
            c2 = conclib.manatee.Corpus(self.abs_corpname(l2_corpname))
        except conclib.manatee.CorpInfoNotFound as e:
            return {'error': 'L2 corpus not found'}
        c1_attr = self._corp().get_conf('BIDICTATTR')
        c2_attr = c2.get_conf('BIDICTATTR')
        tr = Translator(os.path.join(
                self._corp().get_conf('PATH'),
                "bidict." + l2_corpname.split('/')[-1] + "." + c1_attr + "." + c2_attr))
        if tr is not None:
            return {'bidict': tr.records}
        else:
            return {'error': 'Empty bilingual dictionary'}

    def biterms(self, corpname='', l2_corpname='', limit=100, alnum=0, onealpha=1, wlpat='.*', examples_no=0):

        note = ''
        if limit > self._keyword_max_size:
            note = f'You requested {limit} items but you are allowed to see only {self._keyword_max_size} items.'
            limit = self._keyword_max_size

        corp_locale = self._corp().get_conf('DEFAULTLOCALE')
        corp_encoding = self._corp().get_conf('ENCODING')
        def can_return(word_1, word_2, filters):
            for f in filters:
                pattern = regexp_pattern(f, corp_locale, corp_encoding)
                if not bool(pattern.match(word_1) and pattern.match(word_2)):
                    return False
            return True

        filters = [wlpat]
        if alnum:
            filters.append(r"^[\w\- ]+$")
        if onealpha:
            filters.append(r"^.*(?![\d])\w.*$")

        try:
            bitgen = corplib.get_biterms(
                self._corp(),
                l2_corp=self.cm.get_Corpus(l2_corpname),
                limit=limit,
            )
        except Exception as e:
            return {
                "error": repr(e),
                "message": "An error occurred when extracting bilingual terminology",
            }
        lexicon_list = []
        lexicon_dict = defaultdict(list)
        for b in bitgen:
            if can_return(b[0], b[1], filters):
                if b[0] not in lexicon_dict:
                    lexicon_list.append(b[0])
                lexicon_dict[b[0]].append(b)

        return {
            "aligned_corpname": l2_corpname,
            "Biterms": lexicon_list,
            "BitermsDict": lexicon_dict,
            "limit": limit,
            "note": note,
        }

    
    def par_gdex_examples(self, terms=[], corpname='', l2_corpname='', number=1, kwic=1):
        """
        Extract N examples sentences sorted by GDEX score and their aligned parts.
        look to reference corpus
        :param corp_name_l1: str, source corpus name
        :param corp_name_l2: str, target corpus name
        :param term1: str, source term
        :param term2: str, target term
        :param number: int
        :return: list
        """

        # raise Exception(self.corpname)
        out = {'Biterm_examples': {}}
        l2_corp = l2_corpname.strip().split('/')[-1]
        for term1, term2 in terms:
            conc = gdex_examples(self._corp(), f'[term("{term1}")] within {l2_corp}:[term("{term2}")]', number)
            examples_l1 = strkwiclines(conc, 0, number, '1:s', '1:s')
            conc.switch_aligned(conc.orig_corp.get_conffile())
            conc.add_aligned(l2_corp)
            conc.switch_aligned(l2_corp)
            examples_l2 = strkwiclines(conc, 0, number, '1:s', '1:s')

            out['Biterm_examples'][f'({term1},{term2})'] = []
            for i in range(number):
                try:
                    if examples_l1[i].get('kwic') and examples_l2[i].get('kwic'):
                        if kwic:
                            out['Biterm_examples'][f'({term1},{term2})'].append([examples_l1[i],examples_l2[i]])
                        else:
                            out['Biterm_examples'][f'({term1},{term2})'].append([sentence(examples_l1[i]['left'] + examples_l1[i]['kwic'] + examples_l1[i]['right']),
                                                                       sentence(examples_l2[i]['left'] + examples_l2[i]['kwic'] + examples_l2[i]['right'])])
                        
                except IndexError:
                    pass

        return out

    def trends(self, structattr='', trends_attr='word', usesubcorp='',
            trends_method='mkts_all', trends_re='.*', trends_sort_by='t',
            filter_capitalized=1, trends_maxp=0.1, filter_nonwords=1,
            trends_minfreq=5, trends_max_items=1000, filter_by_trend=0,
            trends_order='asc'):
        subcpath = getattr(self._corp(), 'spath', '')
        result, samples = corplib.get_trends(self._corp(), structattr,
                trends_attr, subcpath, trends_re, trends_sort_by,
                filter_nonwords, filter_capitalized, trends_method, trends_maxp,
                trends_minfreq, trends_max_items, filter_by_trend, trends_order)
        if result is None: # trends not computed
            missing_norms = False
            missing_freqs = False
            if usesubcorp:
                missing_norms = not os.path.exists(subcpath[:-5] + '.' +\
                        structattr + '.token')
                missing_freqs = not os.path.exists(subcpath[:-5] + '.' +\
                        trends_attr + '.frq')
            else:
                missing_norms = not os.path.exists(os.path.join(self._corp().get_conf('PATH'),\
                        structattr + '.token'))
            if missing_freqs:
                bgjob = corplib.compute_freqfile(self._user, self._corp(),
                        trends_attr, 'frq', self.get_url())
                if bgjob:
                    return bgjob
            if missing_norms:
                return corplib.compute_norms(self._corp(), self._user,\
                        structattr.split('.')[0], subcpath, self.get_url())
            return corplib.compute_trends(self._corp(), self._user,
                    structattr, trends_attr, trends_method, subcpath, self.get_url())
        if result is False: # computing
            return {'processing': 1, 'result': []}
        if not result: # empty result
            return {'result': [], 'message': "No data for these parameters"}
        attr_label = self._corp().get_conf(trends_attr + '.LABEL') or trends_attr
        return {'result': result, 'samples': samples, 'structattr': structattr,
                'trends_attr': trends_attr, 'usesubcorp': usesubcorp,
                'trends_attr_label': attr_label, 'trends_maxp': trends_maxp,
                'trends_method': trends_method, 'trends_sort_by':trends_sort_by}

    def poswordlist(self, wlpat='', wltype='simple', ref_corpname='',
            ref_usesubcorp='', wlpage=1, lpos=''):
        attrlist = self._corp().get_conf('ATTRLIST').split(',')
        wlattr = None
        for attr in ['lempos', 'wordpos', 'stempos']:
            if attr in attrlist:
                wlattr = attr
                break;
        if not wlattr:
            return {'error': 'PoS wordlist not available for this corpus'}
        self.wlpat = (wlpat or '.*') + lpos
        if wlattr + '_lc' in attrlist and self.wlicase:
            self.wlpat = self.wlpat.lower()
            self.wlattr = wlattr + '_lc'
        else:
            self.wlattr = wlattr
        poswl = self.wordlist(self.wlpat, wltype, self.corpname, self.usesubcorp,
                ref_corpname, ref_usesubcorp, wlpage=wlpage)
        for i in poswl.get('Items', []):
            i['str'] = i['str'][:-2]
        return poswl

    def wsposlist(self):
        return {'wsposlist': [(x['n'], x['v'])\
                for x in corplib.get_wsposlist(self._corp())]}

    def wikisearch(self, query='', langid='en'):
        import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, json
        url = 'http://%s.wikipedia.org/w/api.php?action=query&list=search&'\
                'format=json&srsearch=%s'#&srprop=titlesnippet'
        h = {'User-Agent': 'Sketch Engine Terminology Extraction/1.0 '\
                '(https://app.sketchengine.eu; support@sketchengine.co.uk)'}
        req = urllib.request.Request(url % (langid, urllib.parse.quote_plus(query)),
                headers=h)
        f = urllib.request.urlopen(req)
        d = f.read().decode()
        f.close()
        return json.loads(d)

    def compare_attr(self, corpname='', corpname2='', attr='', attr2=''):
        import pickle
        if len(attr2) == 0:
            attr2 = attr
        if corpname > corpname2:
            corpname, corpname2 = corpname2, corpname
            attr, attr2 = attr2, attr

        try:
            with open("%s/cmp_only-%s-%s-%s.pickle" % (manatee.Corpus(corpname).get_conf("PATH"), corpname2, attr, attr2), "rb") as file_dif:
                dif = pickle.load(file_dif)
        except FileNotFoundError:
            # Check if corpnames are valid and attribute exist in both corpora
            manatee.Corpus(corpname).get_attr(attr)
            manatee.Corpus(corpname2).get_attr(attr)

            return corplib.run_bgjob(self._user, self._corp(), "compare_only.py -c1 %s -c2 %s -a1 %s -a2 %s" % (corpname, corpname2, attr, attr2), "[IGNORE THIS] Attr %s and %s compare on %s and %s" % (attr, attr2, corpname, corpname2), self.get_url())

        dif["order"] = [corpname, corpname2]
        return dif

    def compare_token(self, corpname='', corpname2=''):
        import pickle
        if corpname > corpname2:
            corpname, corpname2 = corpname2, corpname

        try:
            with open("%s/cmp_token-%s.pickle" % (manatee.Corpus(corpname).get_conf("PATH"), corpname2), "rb") as file_dif_token:
                dif_token = pickle.load(file_dif_token)
        except FileNotFoundError:
            c1 = manatee.Corpus(corpname)
            c2 = manatee.Corpus(corpname2)
            s1 = c1.get_struct("s")
            s2 = c2.get_struct("s")
            if s1.size() != s2.size():
                raise Exception("Corpora are not aligned.")

            return corplib.run_bgjob(self._user, self._corp(), "compare_token.py -c1 %s -c2 %s" % (corpname, corpname2), "[IGNORE THIS] Token compare on %s and %s" % (corpname, corpname2), self.get_url())
        except Exception as e:
            return str(e)
        return {"order": [corpname, corpname2], "result": dif_token}
