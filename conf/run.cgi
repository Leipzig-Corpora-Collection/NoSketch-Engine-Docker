#!/usr/bin/python3
# -*- Python -*-
# Copyright (c) 2003-2020  Pavel Rychly, Vojtech Kovar, Milos Jakubicek,
#                          Vit Baisa

import cgitb; cgitb.enable()

import sys, os

if '/usr/lib/python3/dist-packages' not in sys.path:
    sys.path.insert (0, '/usr/lib/python3/dist-packages')

if '/usr/lib/python3/dist-packages/bonito' not in sys.path:
    sys.path.insert (0, '/usr/lib/python3/dist-packages/bonito')

try:
    from wseval import WSEval
except:
    from conccgi import ConcCGI
    from usercgi import UserCGI
    class WSEval(ConcCGI):
        pass

from conccgi import USER_SCOPED_CORPORA_SEP

# Following might be needed for CORS compliance if XHR requests are coming from a different domain
# You may also set it in the webserver configuration instead, see the .htaccess file in
# Bonito distribution tarball for an Apache-based example
#
#print('Access-Control-Allow-Origin: http://localhost:3001')
#print('Access-Control-Allow-Credentials: true')
#print('Access-Control-Allow-Headers: content-type')

from conccgi import ConcCGI
from usercgi import UserCGI
# wmap must be imported before manatee

class BonitoCGI (WSEval, UserCGI):

    _anonymous = True
    _superusers = []

    _data_dir = '/var/lib/bonito'

    # UserCGI options
    _options_dir = _data_dir + '/options'
    _job_dir = _data_dir + '/jobs'

    # ConcCGI options
    _cache_dir = _data_dir + '/cache'
    _tmp_dir = _data_dir + '/tmp'
    subcpath = [_data_dir + '/subcorp/GLOBAL']
    gdexpath = [] # [('confname', '/path/to/gdex.conf'), ...]
    user_gdex_path = "" # /path/to/%s/gdex/ %s to be replaced with username

    # Read corpora list runtime from registry
    # set available corpora, e.g.: corplist = ['susanne', 'bnc', 'biwec']
    if 'MANATEE_REGISTRY' not in os.environ:
        # TODO: SET THIS APROPRIATELY!
        os.environ['MANATEE_REGISTRY'] = '/corpora/registry'
    corplist = [
        corp_name
        for corp_name in os.listdir(os.environ['MANATEE_REGISTRY'])
        if not corp_name.endswith(".disabled") and os.path.isfile(os.path.join(os.environ['MANATEE_REGISTRY'], corp_name))
    ]
    corplist_scoped = [
        os.path.join(scope, corp_name)
        for scope in os.listdir(os.environ['MANATEE_REGISTRY'])
        if not scope.endswith(".disabled") and os.path.isdir(os.path.join(os.environ['MANATEE_REGISTRY'], scope))
        for corp_name in os.listdir(os.path.join(os.environ['MANATEE_REGISTRY'], scope))
        if os.path.isfile(os.path.join(os.environ['MANATEE_REGISTRY'], scope, corp_name))
    ]
    corplist += corplist_scoped
    del corplist_scoped

    # set default corpus
    if len(corplist) > 0:
        corpname = corplist[0]
    else:
        corpname = 'susanne'
    err_types_select = False

    def __init__ (self, user=None):
        if user:
            self._ca_user_info = None
        UserCGI.__init__ (self, user)
        ConcCGI.__init__ (self)

    def _user_defaults (self, user):
        if user is not self._default_user:
            self.subcpath.append (self._data_dir + '/subcorp/%s' % user)
        self._conc_dir = self._data_dir + '/conc/%s' % user
        self._wseval_dir = self._data_dir + '/wseval/%s' % user

    def _setup_user (self):
        # update user infos
        UserCGI._setup_user(self)
        # filter corplist to only include corpora that user is allowed to see
        self.corplist[:] = [
            corp_name
            for corp_name in self.corplist
            # free, public corpora
            if USER_SCOPED_CORPORA_SEP not in corp_name
            # being superuser
            or self._superuser
            # or only my corpora if not anonymous
            or (not self._anonymous and corp_name.split(USER_SCOPED_CORPORA_SEP, 1)[0] == self._user)
        ]

    # corpus access check
    def parse_parameters (self, selectorname=None, environ=os.environ, post_fp=None):
        named_args = super().parse_parameters(selectorname=selectorname, environ=environ, post_fp=post_fp)
        corpname = named_args.get("corpname", None)
        if corpname and corpname not in self.corplist:
            raise ValueError("Corpus '%s' is not available to user!" % corpname)
        return named_args


if __name__ == '__main__':
    # use run.cgi <url> <username> for debugging
    if len(sys.argv) > 1:
        from urllib.parse import urlsplit
        us = urlsplit(sys.argv[1])
        os.environ['REQUEST_METHOD'] = 'GET'
        os.environ['REQUEST_URI'] = sys.argv[1]
        os.environ['PATH_INFO'] = "/" + us.path.split("/")[-1]
        os.environ['QUERY_STRING'] = us.query
    if len(sys.argv) > 2:
        username = sys.argv[2]
    else:
        username = None

        # process optional Authorization header
        if os.environ.get("HTTP_AUTHORIZATION", "").lower().startswith("basic "):
            import base64, subprocess

            digest = os.environ.pop("HTTP_AUTHORIZATION").split(" ", 1)[-1]
            _username, _password = base64.b64decode(digest).decode("utf-8").split(":", 1)
            proc = subprocess.run(["htpasswd", "-vb", "/var/lib/bonito/htpasswd", _username, _password], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            if proc.returncode == 0:
                os.environ["REMOTE_USER"] = _username
            del _username, _password, digest, proc

    if 'MANATEE_REGISTRY' not in os.environ:
        # TODO: SET THIS APROPRIATELY!
        os.environ['MANATEE_REGISTRY'] = '/corpora/registry'

    BonitoCGI(user=username).run_unprotected (selectorname='corpname')

# vim: ts=4 sw=4 sta et sts=4 si tw=80:
