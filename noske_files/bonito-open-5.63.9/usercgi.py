# Copyright (c) 2004-2019  Pavel Rychly, Vojtech Kovar, Milos Jakubicek
#                          Vit Baisa

import CGIPublisher
import os, json
import re
from butils import open_exclusive_file_with_wait
from jobrunner import JobClient

def load_opt_file (options, filepath, option_list=[], selector=''):
    if not os.path.isfile (filepath):
        return
    read_options = {}
    for line in open (filepath).readlines():
        if line[0] == '#':
            continue
        try:
            a, v = line.split ('\t', 1)
        except ValueError:
            continue
        attr = a.strip()
        read_options[attr] = v.strip('\n')
    if selector: CGIPublisher.choose_selector(read_options, selector)
    for k, v in list(read_options.items()):
        if not option_list or k in option_list:
            if v.startswith(("{", "[")):
                try:
                    options[k] = json.loads(v)
                except ValueError:
                    continue
            else: options[k] = v

def set_inner_value(options, path, new_value):
    # throws IndexError, KeyError, TypeError
    import copy
    path_list = path.split('|')
    path0_list = path_list[0].split('[')
    option = path0_list[0]
    whole_value = copy.copy(options.get(option, {}))
    curr_value = whole_value
    curr_key = None
    for it in path0_list[1:] + path_list[1:]: # find the object to set
        for item in it.split('['):
            if curr_key is None: next_value = curr_value
            else: next_value = curr_value[curr_key]
            if item == '__delete':
                if curr_key is None: whole_value = ''
                else: del curr_value[curr_key]
            elif item == '__append':
                if curr_key is None:
                    if whole_value == {}: whole_value = []
                    whole_value.append(new_value)
                else:
                    if curr_value[curr_key] == {}: curr_value[curr_key] = []
                    curr_value[curr_key].append(new_value)
            elif item.endswith(']'): # number
                num = int(item[:-1])
                if not next_value:
                    if curr_key is None:
                        next_value = whole_value = [{}]
                    else:
                        curr_value[curr_key] = [{}]
                curr_value = next_value
                curr_key = num
            else: # key
                if not item in next_value:
                    next_value[item] = {}
                curr_value = next_value
                curr_key = item
    if type(0)==type(curr_key) and type({})==type(curr_value):
        raise IndexError('int in dict not allowed here')
    if item not in ('__delete', '__append'):
        curr_value[curr_key] = new_value
    return option, whole_value


class UserCGI (CGIPublisher.CGIPublisher):
    _ca_user_info = ''
    _ca_api_info = ''
    _options_dir = ''
    _email = ''
    _default_user = 'defaults'
    _superuser = False
    _admin_email = ''
    _from_email = ''
    _mail_server = 'localhost'
    _job_server = 'localhost'
    _job_port = 8333
    _job_dir = ''
    _job_autostart = True
    _data_dir = ''
    _job_prefix = 'localhost'
    _lexonomy_url = 'https://www.lexonomy.eu'
    user_gdex_path = ''
    # list of usernames granted access to job management
    _superusers = []
    attrs2save = []

    def __init__ (self, user=None):
        CGIPublisher.CGIPublisher.__init__ (self)
        self._user = user
        if not self._admin_email:
            self._admin_email = os.environ.get("SERVER_ADMIN", "root@localhost")
        if not self._job_dir:
            self._job_dir = os.path.dirname (os.path.abspath(self._cache_dir))\
                                             + "/jobs"
        if not os.path.isdir(self._job_dir):
            os.makedirs(self._job_dir)
        self._job = JobClient (self._job_server, self._job_port, self._job_dir,\
                               self._admin_email, self._job_prefix,
                               self._email, self._user, self._superuser, self._job_autostart)

    def _user_defaults (self, user):
        pass

    api_key = ''
    url_username = ''
    user_options = {}

    def _setup_user (self):
        if not self._user:
            self._user = os.getenv('HTTP_X_USERNAME')
        if not self._user:
            self._user = os.getenv('REMOTE_USER')
        if not self._user:
            self._user = self._default_user
            self._anonymous = True
        else:
            self._anonymous = False
        self._job.user = self._user
        if self._user in self._superusers: # not needed when CA
            self._job.superuser = self._superuser = True
        user = self._user
        if os.getenv('HTTP_X_WORDLIST_MAX_SIZE'):
            self._wordlist_max_size = int(os.getenv(
                                          'HTTP_X_WORDLIST_MAX_SIZE'))
        if os.getenv('HTTP_X_KEYWORD_MAX_SIZE'):
            self._keyword_max_size = int(os.getenv(
                                          'HTTP_X_KEYWORD_MAX_SIZE'))
        self.annotation_group = os.getenv('HTTP_X_ANNOTATIONGROUP', '')\
                or ('user_' + self._user)
        options = {}
        # TODO: remove when useropts is in place
        load_opt_file (options, os.path.join (self._options_dir,
                                              self._default_user))
        if user is not self._default_user:
            load_opt_file (options, os.path.join (self._options_dir, user))
            self.user_options = options
        CGIPublisher.correct_types (options, self.defaults, selector=1)
        self._user_defaults (user)
        self.__dict__.update (options)

    def reset_user_options(self, corpus=''):
        if self._user == self._default_user:
            return {'error': 'it is not allowed to rewrite defaults'}
        opt_filepath = os.path.join(self._options_dir, self._user)
        if not os.path.exists(opt_filepath):
            return {'status': 'OK'}
        if not corpus: # delete everything
            open(opt_filepath, 'w').close()
            return {'status': 'OK'}
        filt = corpus + ':'
        target = open_exclusive_file_with_wait(opt_filepath + '.tmp.copy')
        source = open(opt_filepath)
        for line in source:
            if not line.startswith(filt):
                target.write(line)
        source.close()
        target.close()
        os.rename(opt_filepath + '.tmp.copy', opt_filepath)
        return {'status': 'OK'}

    def get_user_options(self, options=[], corpus=''):
        defaults = dict([(opt, self.defaults[opt]) for opt in options
                                                   if opt in self.defaults])
        user_opts = {}
        for opt in options:
            if corpus:
                fullopt = '%s:%s' % (corpus, opt)
            else:
                fullopt = opt
            if fullopt in self.user_options:
                user_opts[opt] = self.user_options[fullopt]
        return {'default': defaults, 'user': user_opts}

    def set_user_options(self, options={}, corpus=''):
        def natural_key(x):
            return [ int(s) if s.isdigit() else s
                     for s in re.split(r'(\d+)', x[0]) ]
        if self._user == self._default_user:
            return {'error': 'it is not allowed to rewrite defaults'}
        opt_filepath = os.path.join (self._options_dir, self._user)
        result_options = {}
        load_opt_file(result_options, opt_filepath)
        for k, v in sorted(list(options.items()), key=natural_key, reverse=True):
            option = k
            if corpus:
                k = corpus + ':' + k
            if '|' in k or '[' in k: # parse json path
                try:
                    k, v = set_inner_value(result_options, k, v)
                except (IndexError, KeyError, TypeError):
                    return {'error': k}
            if (k in result_options and v == self.defaults.get(option, '')):
                del result_options[k]
            elif v != self.defaults.get(option, ''): # save only non-default
                result_options[k] = v
        if not os.path.isdir(self._options_dir):
            os.makedirs(self._options_dir)

        try:
            target = open_exclusive_file_with_wait(opt_filepath + '.tmp.copy')
        except FileExistsError:
            os.remove(opt_filepath + '.tmp.copy')
            target = open_exclusive_file_with_wait(opt_filepath + '.tmp.copy')

        for k, v in sorted(result_options.items()):
            if type({}) == type(v) or type([]) == type(v):
                v = json.dumps(v)
            target.write(str(k) + '\t' + str(v) + '\n')
        target.close()
        os.rename(opt_filepath + '.tmp.copy', opt_filepath)

        return {'status': 'OK'}

    def feedback(self, feedback_url='', navigator='', feedback_corpname='',
                 feedback_text='', attachment=('', None), feedback_fullname='',
                 feedback_error='', feedback_email=''):
        def send_mail(subject, msg, sender, recipient, attachment, sender_name, replyto, mailserver):
            import smtplib
            import urllib.request, urllib.parse, urllib.error
            server = smtplib.SMTP(mailserver)
            msg = urllib.parse.unquote(msg).encode('utf-8')
            #from email.MIMEMultipart import MIMEMultipart
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email.mime.text import MIMEText
            from email.utils import formatdate
            from email import encoders
            m = MIMEMultipart('alternative')
            m['From'] = 'Sketch Engine Feedback <%s>' % sender
            m['To'] = recipient
            m['Sender'] = sender
            m['Reply-To'] = replyto
            m['Date'] = formatdate(localtime=True)
            m['Subject'] = subject
            m.attach(MIMEText(msg, _charset="utf-8"))
            if attachment[0]:
                part = MIMEBase('application', "octet-stream")
                part.set_payload(attachment[1].read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="%s"'%\
                        attachment[0])
                m.attach(part)
            server.sendmail(sender, [recipient], m.as_string())
            server.quit()

        if not navigator:
            return {'error': 'Bad request'}
        replyto = self._email or feedback_email or ''
        msg = "%s\n\nUSER %s/%s\nMAIL %s\nCORP %s\nERR %s\nURL %s\nNAV: %s" %\
                (feedback_text, self._user, feedback_fullname, replyto,
                feedback_corpname, feedback_error, feedback_url, navigator)
        sender = self._from_email or self._admin_email
        send_mail('Sketch Engine feedback from %s' % self._user, msg,
                sender, self._admin_email, attachment, self._user, replyto, self._mail_server)
        return {'message': 'ok'}

    def jobs (self, finished=False):
        jobs = self._job.request ("list_user_jobs",
                                  {"user" : self._user, "finished" : finished})
        jobs = json.loads(jobs[0])
        out = {'jobs': jobs, 'view_type' : 'user', 'no_corpus_show': 1}
        return out

    def all_jobs (self, finished=False):
        if not self._superuser:
            raise Exception('access denied: User "%s" is not a superuser' \
                             % self._user)
        jobs = self._job.request ("list_all_jobs",
                                  {"user" : self._user, "finished" : finished})
        jobs = json.loads(jobs[0])
        out = {'jobs': jobs, 'view_type' : 'all', 'no_corpus_show': 1}
        return out

    def jobproxy (self, task=""):
        qs = self.__dict__["environ"]["QUERY_STRING"]
        disallowed_tasks = ["new_job", "list_all_jobs", "list_user_jobs"]
        if task in disallowed_tasks:
            raise Exception('access denied: task not allowed for proxy')
        import re, json
        qs = re.sub ("task=[^;&]+[&;]?", "", qs)
        jr = self._job.request(task, qs)
        return {'signal': jr[0], 'code': jr[1]}

    def get_url(self):
        return getattr(self, 'results_url', '') or self.get_own_url()

    def get_own_url(self):
        scheme = self.environ.get ("REQUEST_SCHEME")
        if not scheme:
            scheme = self.environ.get ("HTTPS") and "https" or "http"
        return "%s://%s%s" % (scheme, self.environ["SERVER_NAME"],
                                      self.environ["REQUEST_URI"])

    def session(self):
        dic = {
            'user_type': 'ANONYMOUS',
            'superuser': self._superuser
        }
        if not self._anonymous:
            dic['user_type'] = 'FULL_ACCOUNT'
            dic['user'] = {
                'id': 0,
                'username': self._user,
                'active': True,
                'email': self._email,
                'full_name': '',
                'first_name': '',
                'last_name': '',
                'space_used': 0,
                'space_total': 0,
                'email_verified': True,
                'academic': True,
                'elexis': False,
                'elexis_agreed': True,
                'privacy_consent': True,
                'licence_type': '',
                'administered_site_licences': [],
                'tbl_templates': [],
                'organisation': '',
                'country': '',
                'invoice_address': '',
                'vat_number': '',
                'api_key': None,
                'date_joined': None
            }
        return {'data': dic}
