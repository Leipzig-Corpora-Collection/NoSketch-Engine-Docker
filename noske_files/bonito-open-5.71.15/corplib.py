#!/usr/bin/python3
# Copyright (c) 2003-2019  Pavel Rychly, Vojtech Kovar, Milos Jakubicek
#                          Milos Husak, Vit Baisa

import manatee
import os, sys, glob
import time
from manatee import regexp_pattern

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5
from butils import *

DEFAULTMAXLISTSIZE = 150

class CorpusManager:
    def __init__ (self, corplist=['susanne'], subcpath=[], gdexpath=[],
                  jobclient=None, abs_corpname=None):
        self.corplist = corplist
        self.subcpath = subcpath
        self.gdexdict = dict(gdexpath)
        self.user_gdex_path = ""
        self.missing_subc_error = ''
        self.jobclient = jobclient
        self.obsolete_subcorp = ''
        self.obsolete_has_subcdef = False
        self.abs_corpname = abs_corpname

    def get_gdex_conf_path(self, conf):
        if not self.user_gdex_path:
            return self.gdexdict.get(conf, "")
        return conf and os.path.join(self.user_gdex_path, conf) or ""

    def default_subcpath(self, corp):
        if type(corp) in (type(''), type('')): corp = self.get_Corpus (corp)
        if corp.get_conf('SUBCBASE'): return corp.get_conf('SUBCBASE')
        cpath = corp.get_conf('PATH')
        return os.path.join(cpath, 'subcorp')

    def get_Corpus (self, corpname, subcname='', complement=False):
        if ':' in corpname:
            corpname, subcname = corpname.split(':',1)
        corp = manatee.Corpus (self.abs_corpname(corpname))
        manatee.setEncoding(corp.get_conf('ENCODING'))
        corp.corpname = str(corpname) # never unicode (paths)
        corp.cm = self
        dsubcpath = self.default_subcpath (corp)
        if subcname:
            import urllib.request, urllib.parse, urllib.error
            user_subcpath = self.subcpath[-1]
            qsubcname = urllib.parse.quote_plus(subcname)
            for sp in self.subcpath + [dsubcpath]:
                if sp == dsubcpath:
                    spath = os.path.join (sp, qsubcname + '.subc')
                else:
                    spath = os.path.join (sp, corpname, qsubcname + '.subc')
                if os.path.isfile (spath):
                    sctime = time.gmtime(os.stat(spath).st_mtime)
                    dafile = os.path.join(corp.get_conf('PATH'),
                            corp.get_conf('DEFAULTATTR') + '.lex')
                    if user_subcpath in spath and sctime < time.gmtime(os.stat(dafile).st_mtime):
                        self.obsolete_subcorp = subcname
                        if os.path.exists(spath + 'def'):
                            self.obsolete_has_subcdef = True
                    subc = manatee.SubCorpus (corp, spath, complement)
                    subc.corp = corp
                    subc.spath = spath
                    try: open(spath[:-4] + 'used', 'w')
                    except: pass
                    subc.corpname = str(corpname) # never unicode (paths)
                    subc.subcname = subcname
                    subc.cm = self
                    if os.path.exists(spath + 'def'):
                        subc.subcdef = parse_subcdef(qsubcname, spath + 'def')
                    else:
                        subc.subcdef = [qsubcname, "", ""]
                    compl = complement and b'1' or b''
                    subc.subchash = md5(open(spath, 'rb').read()+compl).digest()
                    return subc
                elif os.path.exists(spath + 'def'):
                    self.obsolete_subcorp = subcname
                    self.obsolete_has_subcdef = True
                    self.subcdef = parse_subcdef(qsubcname, spath + 'def')
                    break
            if not self.obsolete_subcorp or not self.obsolete_has_subcdef:
                self.missing_subc_error = 'Subcorpus "%s" not found' % subcname
            return corp
        else:
            return corp

    def corplist_with_names (self, conf_options=[]):
        """conf_options
           -- list of options to be extracted from corpus configure files"""
        cl = []
        for c in self.corplist:
            try:
                mc = manatee.Corpus(self.abs_corpname(c))
                cinf = {'id': c,
                        'name': mc.get_conf('NAME') or c}
                cinf.update([(o.lower(), mc.get_conf(o)) for o in conf_options])
            except:
                cinf = {'id': c, 'name': c}
            cl.append (cinf)
        return sorted(cl, key=lambda d: d['id']) 

    def subcorpora (self, corpname):
        # we must encode for glob.glob otherwise it fails for non-ascii files
        subc = []
        for sp in self.subcpath:
            subc += [(x, 1) for x in\
                    glob.glob(os.path.join(sp, corpname, '*.subc'))]
            subc += [(x, 2) for x in\
                    glob.glob(os.path.join(sp, corpname, '*.subcdef'))\
                    if not os.path.exists(x[:-3])]
        subc += [(x, 0) for x in glob.glob(os.path.join(\
                self.default_subcpath(corpname), '*.subc'))]
        return subc

    def subcorp_names (self, corpname, subcorp_id2name={}):
        from urllib.parse import unquote_plus
        out = []
        for s in self.subcorpora(corpname):
            subc_id = unquote_plus(os.path.splitext(os.path.basename(s[0]))[0])
            name = subcorp_id2name.get(subc_id, subc_id)
            if not subc_id.startswith("###") and not subc_id.endswith("###"):
                out.append({'n': subc_id, 'name': name, 'user': s[1]})
        return sorted(out, key=lambda x:x['n'])

    def find_same_subcorp_file (self, corpname, scpath, user="**", attr=None, frqtype=None, subcfilter="*"):
        basedir = os.path.dirname (self.subcpath[-1].rstrip('/'))
        scsize = os.path.getsize (scpath)
        scdata = open(scpath, "rb").read()
        if frqtype:
            frqtype = frqtype.split(":")[0]

        for f in glob.glob (basedir + '/%s/%s/%s.subc' % (user, corpname, subcfilter), recursive=True):
            if f == scpath: continue
            if os.path.getsize(f) != scsize: continue
            if frqtype:
                filename = f[:-4] + attr + '.' + frqtype
            else:
                filename = f
            if not os.path.isfile(filename):
                continue
            # now, f has same size and the required freq file exists
            if open(f, "rb").read() == scdata:
                return f
        return None

def corpconf_pairs (corp, label):
    val = corp.get_conf(label)
    if len(val) > 2:
        val = val[1:].split(val[0])
    else:
        val = ''
    return [val[i:i+2] for i in range (0, len(val), 2)]

def get_wsposlist(corp):
    wsdef = corp.get_conf('WSDEF')
    if wsdef:
        wsp_line = [ll for ll in open(wsdef) if ll.startswith('*WSPOSLIST')]
        if wsp_line:
            val = wsp_line[0].strip()[11:].strip('"')
            vallist = val[1:].split(val[0])
            return [{'n':vallist[i], 'v':vallist[i+1]}
                    for i in range (0, len(vallist), 2)]
    return [{'n':x[0], 'v':x[1]} for x in corpconf_pairs(corp, 'WSPOSLIST')]


def get_alt_lpos_data(data, ind):
    lpos = data[ind][3]
    lempos = data[ind][2]
    wid = data[ind][1]
    lemma = data[ind][4]
    ws_status = data[ind][5]
    return lpos, lempos, wid, lemma, ws_status


def get_alt_lposes(corp, lemma, wsattr):
    # try locating all lemposes for lemma
    ret = []
    wsposlist = [lpos['v'] for lpos in get_wsposlist(corp)] or ['']
    gen = wsattr.regexp2ids(lemma + '-.', False)
    while not gen.end():
        a_id = gen.next()
        s = wsattr.id2str(a_id)
        ret.append([wsattr.freq(a_id), a_id, s, s[-2:], lemma])
    # if nothing was found, use MAPTO to obtain lemposes
    defattr = corp.get_attr(corp.get_conf("DEFAULTATTR"))
    if not ret and wsattr.name != defattr.name:
        try:
            attrmap = corp.get_attr(defattr.name + '@' + wsattr.name)
            wid = defattr.str2id(lemma)
        except:
            try:
                attrmap = corp.get_attr('word@' + wsattr.name)
                wid = corp.get_attr('word').str2id(lemma)
            except:
                attrmap = None
        if attrmap and wid >= 0:
            fs = attrmap.dynid2srcids(wid)
            wst = int(corp.get_conf('WSSTRIP'))
            while not fs.end():
                mid = fs.next()
                s = wsattr.id2str(mid)
                if wst:
                    if s[-(wst):] in wsposlist:
                        ret.append([wsattr.freq(mid), mid, s, s[-(wst):], s[:-(wst)]])
                else:
                    ret.append([wsattr.freq(mid), mid, s, '', s])
    if ret:
        ret.sort(reverse=True)
        # throw away low-frequency variants
        maxf = ret[0][0]
        result = []
        for x in ret:
            if x[0]*100 < maxf:
                result.append(x + ['low_freq'])
            elif x[3] not in wsposlist:
                result.append(x + ['not_in_wsposlist'])
            else:
                result.append(x + ['ok'])
        return result
    return []

def attr_vals (corpname, avattr, avpattern, avmaxitems, avfrom, icase=1):
    c = manatee.Corpus (corpname)
    attr = c.get_attr (avattr, True)
    gen = attr.regexp2ids (avpattern.strip(), icase)
    items = []
    while not gen.end() and avmaxitems > 0:
        if avfrom > 0:
            gen.next()
            avfrom -= 1
            continue
        items.append (attr.id2str(gen.next()))
        avmaxitems -= 1
    return {'query': avpattern,
            'suggestions': items,
            'no_more_values': gen.end()}

def texttype_values (corp, subcorpattrs, list_all=False, hidenone=True):
    if subcorpattrs == '#': return []
    attrlines = []
    for subcorpline in subcorpattrs.split(','):
        attrvals = []
        for n in subcorpline.split('|'):
            if n in ('', '#'):
                continue
            slurp = 0
            if n.startswith('*'):
                n = n[1:]
                slurp = 1
            attr = corp.get_attr (n)

            attr_doc = corp.get_conf(n+'.ATTRDOC')
            if attr_doc and os.path.exists(attr_doc):
                with open(attr_doc, 'r') as attr_html:
                    attr_doc = attr_html.read()

            attrval = { 'name': n,
                        'label': corp.get_conf (n+'.LABEL') or n,
                        'attr_doc': attr_doc,
                        'attr_doc_label': corp.get_conf (n+'.ATTRDOCLABEL'),
                      }
            if slurp:
                attrval['slurp'] = 1
                if attrvals: attrvals[-1]['continue'] = 1
            try:
                maxlistsize = int(corp.get_conf (n+'.MAXLISTSIZE'))
            except ValueError:
                maxlistsize = DEFAULTMAXLISTSIZE
            hsep = corp.get_conf(n+'.HIERARCHICAL')
            multisep = ''
            if corp.get_conf(n+'.MULTIVALUE').startswith(('y', 'Y', '1')):
                multisep = corp.get_conf(n+'.MULTISEP')
            if not hsep and not list_all \
                                and (corp.get_conf (n+'.TEXTBOXLENGTH')
                                      or attr.id_range() > maxlistsize):
                attrval ['textboxlength'] = (corp.get_conf (n+'.TEXTBOXLENGTH')
                                             or 24)
            else: # list of values
                if corp.get_conf(n+'.NUMERIC'):
                    vals = []
                    for i in range(attr.id_range()):
                        import re
                        val = attr.id2str(i)
                        numstr = re.match('\\D*(\\d*)', val).group(1)
                        num = 999999999999
                        if numstr:
                            num = int(numstr)
                        vals.append({'v': val, 'sort': num})
                elif hsep: # hierarchical
                    vals = [{'v': attr.id2str(i)}
                                  for i in range(attr.id_range())
                                  if not multisep in attr.id2str(i)]
                else:
                    vals = [{'v': attr.id2str(i)}
                            for i in range(attr.id_range())
                            if not (multisep and multisep in attr.id2str(i))]
                if hidenone: # hide empty + ===NONE===
                    i = 0
                    while i < len(vals):
                        if vals[i]['v'] in ('', '===NONE==='): del vals[i]
                        else: i += 1
                if hsep: # hierarchical
                    attrval ['hierarchical'] = hsep
                    attrval ['Values'] = get_attr_hierarchy(vals, hsep)
                else:
                    vals.sort(key=lambda x: (x.get('sort', 0), x['v']))
                    attrval ['Values'] = vals
            attrvals.append (attrval)
        attrlines.append ({'Line': attrvals})
    return attrlines

def get_attr_hierarchy(vals, hsep):
    result = {}
    values = set([])
    for v in vals:
        values.add(v['v'])
    for value in sorted(values):
        level = result
        while hsep in value:
            key, value = value.split(hsep, 1)
            try: level = level[key]
            except: value = key + hsep + value; break
        level[value] = {}
    return result

def get_freqpath (c, attrname):
    if attrname == "TERM":
        attrname = os.path.basename(c.get_conf("TERMBASE"))
    elif attrname == "WSCOLLOC":
        attrname = os.path.basename(c.get_conf("WSBASE"))
    subcpath = c.get_conf("SUBCPATH")
    if subcpath:
        return subcpath + attrname
    return c.get_conf('PATH') + attrname

def create_mkstats_cmd (corp, attrname, freqtype):
    outfilename = get_freqpath (corp, attrname)
    if os.path.isfile (outfilename + "." + freqtype): # XXX this is not enough, the computation can finish anytime after this call and before jobrunner checks for it, needs to be handled in jobrunner
        return
    path = ""
    if hasattr(corp, 'spath'):
        path = "'%s'" % corp.spath
        same = corp.cm.find_same_subcorp_file (corp.corpname, corp.spath, attr=attrname, frqtype=freqtype)
        if same:
            same = same[:-4] + attrname
            from shutil import copyfile
            freqtype = freqtype.split(":")[0] # e.g. star:f
            copyfile (same + "." + freqtype, outfilename + "." + freqtype)
            try: copyfile (same + '.frq64', outfilename + '.frq64')
            except: pass
            return
    if attrname == "WSCOLLOC":
        cmd = "sortws -q %s" % corp.get_confpath()
        if hasattr(corp, 'spath'): # this should always be the case for WSCOLLOC, but to be safe...
            cmd += " %s" % corp.spath
        return cmd
    return "mkstats %s %s %s %s" % (corp.get_confpath(), attrname, freqtype,
                                    path)

def compute_trends(corp, user, sattr, tattr, method, subcpath, url):
    cmd = "mktrends %s %s %s %s 5 0.15 '%s'" % (corp.get_confpath(), sattr, tattr,
            method, subcpath)
    cmd_desc = corp.get_conf('NAME')
    desc = 'Trends (%s)' % cmd_desc
    return run_bgjob(user, corp, cmd, desc, url)

def compute_norms(corp, user, struct, subcpath, url):
    cmd_desc = corp.get_conf('NAME')
    subcmd = ""
    if subcpath:
        subcmd += "-s '%s'" % subcpath
    cmd = "mktokencov %s %s %s" % (corp.get_confpath(), struct, subcmd)
    desc = "Norms (%s)" % cmd_desc
    return run_bgjob(user, corp, cmd, desc, url)

def compute_ngrams (user, corp, attrname, url):
    from math import log
    th = max(2, int(log(corp.size(), 60))) # dynamic threshold
    cmd = " ".join(['genngr', corp.get_confpath(), attrname, str(th),
                    corp.get_conf("PATH") + attrname + ".ngr"])
    desc = "N-grams computation ('%s' attribute)" % attrname
    return run_bgjob (user, corp, cmd, desc, url)

def get_stat_desc (stat):
    return {'arf':'average reduced frequency',
            'frq':'frequency',
            'docf':'document frequency',
            'rnk':'score'}.get(stat, stat)

def compute_freqfile (user, corp, attrname, freqtype, url):
    freqdesc = get_stat_desc (freqtype)
    cmd = create_mkstats_cmd (corp, attrname, freqtype)
    if not cmd:
        return None
    desc = "(Sub)corpus (%s)" % freqdesc
    return run_bgjob (user, corp, cmd, desc, url)

def run_bgjob (user, corp, cmd, desc, url):
    from urllib.parse import unquote_plus
    job = corp.cm.jobclient.request ("new_job",
            {"cmd" : cmd, "url" : url,
             "corpus" : corp.get_conf("NAME"), "desc" : desc})
    if job[1] == 200: # new process started:
        return {"progress": '0', "jobid": job[0], "notifyme": False,
                "esttime": "N/A", "desc": unquote_plus(desc)}
    else: # already running
        job = corp.cm.jobclient.request ("job_progress", {"jobid" : job[0]})
        import json
        job = json.loads(job[0])
        return {"progress": job[0]["progress"], "jobid": job[0]["jobid"],
                "notifyme": job[0].get("notifyme", False),
                "esttime": job[0]["esttime"], "desc": unquote_plus(desc)}

def get_ws_info(corp):
    info = {
        'mfw': corp.get_conf('WSMFW') or None,
        'mfwf': corp.get_conf('WSMFWF') or None,
    }
    try:
        info['mfwf'] = int(info['mfwf'])
    except:
        pass
    if info['mfw'] is None or info['mfwf'] is None:
        info['mfw'] = info['mfwf'] = None
    return info

def parse_sizes(sizes_string):
    sizes = {}
    alsizes = []
    for sizesline in sizes_string.split('\n'):
        sls = sizesline.strip().split()
        if len(sls) == 2:
            sizes[sls[0]] = int(sls[1])
        elif len(sls) == 4:
            alsizes.append((sls[2], int(sls[1]), int(sls[3])))
    return sizes, alsizes

def get_corp_info(corp, registry=0, gramrels=0, corpcheck=0, struct_attr_stats=0):
    result = {
            'wposlist': corpconf_pairs(corp, 'WPOSLIST'),
            'lposlist': corpconf_pairs(corp, 'LPOSLIST'),
            'wsposlist': [[x['n'], x['v']] for x in get_wsposlist(corp)],
            'attributes': [],
            'structs': [],
            'name': corp.get_conf('NAME'),
            'lang': corp.get_conf('LANGUAGE'),
            'infohref': corp.get_conf('INFOHREF'),
            'info': corp.get_conf('INFO'),
            'handle': corp.get_conf('HANDLE') or None,
            'institution': corp.get_conf('INSTITUTION') or None,
            'encoding': corp.get_conf('ENCODING'),
            'tagsetdoc': corp.get_conf('TAGSETDOC'),
            'defaultattr': corp.get_conf('DEFAULTATTR'),
            'starattr': corp.get_conf('STARATTR'),
            'unicameral': True if corp.get_conf('NOLETTERCASE') == '1' else False,
            'righttoleft': True if corp.get_conf('RIGHTTOLEFT') == '1' else False,
            'errsetdoc': corp.get_conf('ERRSETDOC'),
            'wsattr': corp.get_conf('WSATTR'),
            'wsdef': corp.get_conf('WSDEF'),
            'termdef': corp.get_conf('TERMDEF'),
            'diachronic': list(filter(bool, corp.get_conf('DIACHRONIC').split(','))) or None,
            'aligned': list(filter(bool, corp.get_conf('ALIGNED').split(','))),
            'aligned_details': [],
            'freqttattrs': list(filter(bool, corp.get_conf('FREQTTATTRS').replace('|', ',').replace('*', '').split(','))),
            'subcorpattrs': list(filter(bool, corp.get_conf('SUBCORPATTRS').replace('|', ',').replace('*', '').split(','))),
            'shortref': corp.get_conf('SHORTREF'),
            'fcsrefs': corp.get_conf('FCSREFS') or None,
            'docstructure': corp.get_conf('DOCSTRUCTURE'),
            'newversion': corp.get_conf('NEWVERSION'),
            'structures': [],
            'is_error_corpus': False,
            'structctx': corp.get_conf('STRUCTCTX'),
            'deffilterlink': True if corp.get_conf('DEFFILTERLINK') == '1' else False,
            'defaultstructs': list(filter(bool, corp.get_conf('DEFAULTSTRUCTS').split(','))) or [],
            'wsttattrs': corp.get_conf('WSTTATTRS'),
            'maxcontext': corp.get_conf('MAXCONTEXT'),
            'wsinfo': get_ws_info(corp)
    }
    terms_file = corp.get_conf('TERMBASE') + '.fsa'
    result['terms_compiled'] = os.path.exists(terms_file)
    sizes_file = os.path.join(corp.get_conf('PATH'), "sizes")
    if os.path.exists(sizes_file):
        modtime = time.gmtime(os.stat(sizes_file).st_mtime)
        result['compiled'] = time.strftime("%m/%d/%Y %H:%M:%S", modtime)
        compiled = True
    else:
        result['compiled'] = ''
        compiled = False
    structlist = list(filter(bool, corp.get_conf('STRUCTLIST').split(',')))
    structattr_dict = {}
    for structattr in list(filter(bool, corp.get_conf('STRUCTATTRLIST').split(','))):
        struct, attr = structattr.split('.')
        if struct not in structattr_dict:
            structattr_dict[struct] = []
        structattr_dict[struct].append(attr)
    for struct_name in structlist:
        structure = {
            'name': struct_name,
            'label': corp.get_conf('%s.LABEL' % struct_name),
            'attributes': [],
            'size': ''
        }
        if compiled and struct_attr_stats:
            corps_struct = corp.get_struct(struct_name)
            structure['size'] = corps_struct.size()
        if struct_name in structattr_dict:
            for attr_name in structattr_dict[struct_name]:
                attribute = {
                    'name': attr_name,
                    'label': corp.get_conf('%s.%s.LABEL' % (struct_name, attr_name)),
                    'dynamic': corp.get_conf('%s.%s.DYNAMIC' % (struct_name, attr_name)),
                    'fromattr': corp.get_conf('%s.%s.FROMATTR' % (struct_name, attr_name)),
                    'size': ''
                }
                if compiled and struct_attr_stats:
                    attribute['size'] = corps_struct.get_attr(attr_name).id_range()
                structure['attributes'].append(attribute)
        structure['attributes'].sort(key=lambda x: x['size'], reverse=True)
        result['structures'].append(structure)
    result['structures'].sort(key=lambda x: x['size'], reverse=True)

    if 'err' in structlist and 'corr' in structlist:
        result['is_error_corpus'] = True
    attrlist = corp.get_conf('ATTRLIST').split(',')
    wsdef = corp.get_conf('WSDEF')
    result['gramrels'] = []
    if gramrels and wsdef:
        grl = []
        grspd = {}
        import wmap
        try:
            wsbase = corp.get_conf('WSBASE')
            ws = wmap.WMap(wsbase, corp)
            for i in range(ws.id_range()):
                grn = ws.id2str(i)
                grsp = ws.seppage(i)
                if grsp == -1:
                    grl.append(grn)
                else:
                    grspd.setdefault(grsp, [])
                    grspd[grsp].append(grn)
            result['gramrels'].extend(sorted(grl))
            result['gramrels'].extend([x[1] for x in grspd.items()])
        except RuntimeError:
            pass

    for item in attrlist:
        result['attributes'].append({
            'name': item,
            'id_range': compiled and corp.get_attr(item).id_range() or 0,
            'label': corp.get_conf(item + '.LABEL'),
            'dynamic': corp.get_conf(item + '.DYNAMIC'),
            'fromattr': corp.get_conf(item + '.FROMATTR')
        })
    result['sizes'], result['alsizes'] = parse_sizes(corp.get_sizes())
    if corpcheck:
        from butils import get_last_corpcheck
        logs = sorted(glob.glob(os.path.join(corp.get_conf('PATH'), 'log/*.log')))
        if logs:
            result['last_corpcheck'] = get_last_corpcheck(logs[-1])
    if registry:
        result['registry_dump'] = manatee.loadCorpInfo(corp.cm.abs_corpname(corp.corpname))\
                .dump().replace('\r', '\n')
        result['registry_text'] = open(corp.get_confpath()).read().replace('\r', '\n')
    for al in result['aligned']:
        c = corp.cm.get_Corpus(al)
        attrs = c.get_conf('ATTRLIST').split(',')
        poslist = corpconf_pairs(c, 'WPOSLIST')
        lposlist = 'lempos' in attrs and corpconf_pairs(c, 'LPOSLIST') or poslist
        result['aligned_details'].append({
            'name': c.get_conf('NAME'),
            'language_name': c.get_conf('LANGUAGE'),
            'Wposlist': [{'n': x[0], 'v': x[1]} for x in poslist],
            'Lposlist': [{'n': x[0], 'v': x[1]} for x in lposlist],
            'has_case': c.get_conf('NOLETTERCASE') != '1',
            'has_lemma': 'lempos' in attrs or 'lemma' in attrs,
            'tagsetdoc': c.get_conf('TAGSETDOC')
        })
    return result

def get_biterms(corp, l2_corp=None, limit=1000):
    path = corp.get_conf('PATH')
    if not l2_corp.corpname:
        raise Exception('Aligned corpus not specified')
    fname = os.path.join(path, l2_corp.corpname.split('/')[-1] + '.biterms')
    if not os.path.exists(fname):
        raise Exception('No bilingual terminology for' + ' ' + l2_corp.corpname)
    with open(fname) as f:
        l1t_set = set()
        while len(l1t_set) < limit:
            line = f.readline().strip()
            if not line:
                break
            l1t, l2t, fab, fa, fb, l1s, l2s, ld = line.split('\t')
            l1str = re.sub('-.$', '', l1t.replace("_", " "))
            l2str = re.sub('-.$', '', l2t.replace("_", " "))
            
            # l1t and l2t - strings from *.biters file
            yield [l1str, l2str, int(fab), int(fa), int(fb), float(l1s), float(l2s), float(ld), l1t, l2t]
            l1t_set.add(l1t)

def get_trends(corp, sattr, attr, subcpath, trends_re, sort_by,
        filter_nonwords, filter_capitalized, method,
        maxp, minfreq, trends_max_items, filter_by_trend, trends_order):
    import math
    path = corp.get_conf('PATH')
    corp_locale = corp.get_conf('DEFAULTLOCALE')
    corp_encoding = corp.get_conf('ENCODING')
    if subcpath:
        fpath = subcpath + '.' + '.'.join([sattr, attr, method, 'trends'])
        spath = subcpath + '.' + '.'.join([sattr, attr, method, 'minigraphs'])
    else:
        fpath = os.path.join(path, '.'.join([sattr, attr, method, 'trends']))
        spath = os.path.join(path, '.'.join([sattr, attr, method, 'minigraphs']))
    trends_items, samples = [], {}
    if os.path.exists(fpath):
        if filter_nonwords:
            nwre = re.compile(corp.get_conf('NONWORDRE').replace('^[:alpha:]',
                    '\d\W_'), re.UNICODE)
        if trends_re:
            tre = regexp_pattern(trends_re, corp_locale, corp_encoding)

        a = corp.get_attr(attr)
        a_frq = a.get_stat('frq')
        for _id, angle, p in read_trends_file(fpath):
            if _id == -1:
                return False, []
            if _id == -2:
                return [], []
            w = a.id2str(_id)
            f = a_frq.freq(_id)
            if not w:
                continue
            if minfreq > f or maxp < p:
                continue
            if filter_nonwords and nwre.search(w):
                continue
            if filter_capitalized and w[0].lower() != w[0]:
                continue
            if trends_re and not tre.match(w):
                continue
            trend = math.tan(angle/180.0*math.pi)
            if trend > 1.0:
                simple_trend = 2
            elif trend > 0.1:
                simple_trend = 1
            elif trend > -0.1:
                simple_trend = 0
            elif trend > -1.0:
                simple_trend = -1
            else:
                simple_trend = -2
            if filter_by_trend:
                if filter_by_trend > 0 and trend <= 0:
                    continue
                if filter_by_trend < 0 and trend >= 0:
                    continue
            trends_items.append([_id, w, trend, p, f, simple_trend])
        rev = trends_order == 'desc'
        if sort_by == 'w':
            trends_items.sort(key=lambda x:x[1], reverse=rev)
        elif sort_by == 't':
            trends_items.sort(key=lambda x:abs(x[2]), reverse=rev)
        elif sort_by == 'p':
            trends_items.sort(key=lambda x:x[3], reverse=rev)
        elif sort_by == 'f':
            trends_items.sort(key=lambda x:x[4], reverse=rev)
        del trends_items[trends_max_items:]
        if os.path.exists(spath):
            tids = [x[0] for x in trends_items]
            for sitem in read_trends_file(spath, True):
                if sitem[0] in tids:
                    samples[sitem[0]] = ':'.join(map(str, sitem[1]))
    else:
        return None, None
    return trends_items, samples

def read_trends_file(path, samples=False):
    import struct
    f = open(path, 'rb')
    h = f.read(32)
    if not h: # header empty => computing
        yield samples and (-1, -1) or (-1, -1, -1)
    result = []
    if samples:
        b = f.read(8)
        if b == b'':
            yield (-2, -1) # empty file after header
        while b != b'':
            try:
                _id, v = struct.unpack('<II', b)
            except:
                yield (-1, [])
            cols = [(v >> i & 15) for i in (0, 4, 8, 12, 16, 20, 24, 28)]
            yield (_id, cols)
            b = f.read(8)
    else:
        #hexdump -s 32 -v -e '1/4 "%i" 1/1 " %5i" 1/4 " %10f" "\n"'
        b = f.read(9)
        if b == b'':
            yield (-2, -1, -1) # empty file after header
        while b != b'':
            try:
                _id, angle, p = struct.unpack('<Ibf', b)
                yield (_id, angle, p)
            except Exception as e:
                yield (-1, -1, -1)
            b = f.read(9)

def save_subcdef(path, subcname, structname, subquery):
    scdf = open(path + 'def', 'w')
    scdf.write('=%s\n\t%s\n\t' % (subcname, structname))
    scdf.write(subquery)
    scdf.write('\n')
    scdf.close()
    return path + 'def'

def parse_subcdef(subcname, path):
    "extracts only the first (topmost) subc definition"
    infile = open(path)
    while 1:
        line = infile.readline()
        if not line:
            break
        if line.startswith('='):
            subcdef_subcname = line[1:].strip()
            struct = infile.readline().strip()
            query = infile.readline().strip()
            if subcdef_subcname == subcname and struct and query:
                return (subcdef_subcname, struct, query)
    return (False, False, False)

def are_subcorp_stats_compiled(c, attr, nums='frq'):
    # check subcorpus statistics are compiled for the given attribute
    if isinstance(attr, str):
        attr = c.get_attr (attr)
    try:
        return attr.get_stat(nums)
    except manatee.FileAccessError:
        return False

def has_fsa(corpus, sourcename, sourcetype):
    sizes_file = os.path.join(corpus.get_conf('PATH'), "sizes")
    if not os.path.exists(sizes_file):
        raise RuntimeError ("Corpus data corrupted.")
    desc = "Building FSA for"
    attrs = ("%s,%s" % (corpus.get_conf("ATTRLIST"),corpus.get_conf("STRUCTATTRLIST"))).split(",")
    if sourcetype == "ATTR" and sourcename in attrs:
        prefix = corpus.get_conf("PATH") + sourcename
        if not os.path.isfile(prefix + ".fsa"):
            return ("lex2fsa " + prefix,
                    desc + " attribute " + sourcename)
    elif sourcetype == "NGRAM":
        if not os.path.isfile(corpus.get_conf("PATH") + sourcename + ".wl.fsa"):
            return ("ngr2fsa %s %s" % (corpus.get_confpath(), sourcename[:-4]),
                    desc + " n-grams on attribute " + sourcename[:-4])
    elif sourcetype == "TERM" and corpus.get_conf("TERMDEF"):
        prefix = corpus.get_conf("TERMBASE") # XXX backward compatibility, [:-3] to be removed
        if prefix.endswith("-ws"):
            prefix = prefix[:-3]
        if not os.path.isfile(prefix + ".fsa"):
            return ("terms2fsa %s %s" % (corpus.get_confpath(), prefix), desc + " terms")
    elif sourcetype == "WSCOLLOC":
        prefix = corpus.get_conf("WSBASE")
        if not os.path.isfile(prefix + ".wl.fsa"):
            return ("ws2fsa %s" % corpus.get_confpath(), desc + " word sketch collocations")
    else:
        raise RuntimeError ("Invalid FSA source " + sourcetype + ":" + sourcename)
