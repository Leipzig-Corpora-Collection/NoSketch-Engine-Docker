const {Url} = require("core/url.js")

function createGETURL(url, query){
    url = url || "";
    let queryStr = "";

    if(query){
        if(typeof query == "string"){
            queryStr = query;
        } else if (typeof query == "object") {
            queryStr = getUrlQuery(query);
        }
    }
    if(queryStr){
        return url + (url.indexOf('?') >= 0 ? "&" : "?") + queryStr
    }
    return url
}

function getUrlQuery(queryObj){
    let query = "";
    let val;

    // query can be defined as array or dictionary
    if(Array.isArray(queryObj)){
        queryObj.forEach((q) => {
            query = addToQuery(query, q.key, q.value)
        })
    } else{
        for(let key in queryObj){
            val = queryObj[key];
            if(val !== ""){
                query = addToQuery(query, key, val)
            }
        }
    }
    return query;
}

function addToQuery(query, key, value){
    query += query == "" ? "" : "&"
    query += key + "=" + encodeURIComponent((typeof value == "boolean") ? (value + 0) : value);
    return query;
}

function checkSessionAndRedirect(request, payload, callback){
    if(!window.config.URL_RASPI){
        Dispatcher.trigger("ROUTER_GO_TO", "unauthorized")
    } else {
        Dispatcher.trigger("CHECK_SESSION_AND_REDIRECT", function(request, payload, authorized){
            if(authorized && request.fail){
                request.fail(payload.responseJSON ? payload.responseJSON : payload, request);
            }
            callback && callback(authorized, request, payload)
        }.bind(this, request, payload))
    }
}

class ConnectionClass{
    constructor(){
        // shorter values will be send in query string. Other is post data.
        this.MAX_QUERY_VALUE_LENGTH = 250
        this.lastBonitoVersion = null
        this.activeRequests = []
        this.bonitoNote = Url.getQuery().note || null
        Dispatcher.on("NOTE_CHANGED", note =>{
            this.bonitoNote = note
        })
    }

    get(request){
        if(request.loadingId){
            Dispatcher.trigger("LOADING_CHANGED", true, request.loadingId)
        }

        if (request.data) {
            let method = request.url.startsWith(window.config.URL_BONITO) ? request.url.slice(window.config.URL_BONITO.length) : null
            let corpus = request.data.corpname
            let query =
                (method === "concordance") ? {query: request.data.concordance_query[0][request.data.concordance_query[0].queryselector.slice(0, -3)], extra: `:ps=${request.data.pagesize}`, data: request.data.concordance_query}
                : (method === "wordlist") ? {attr: request.data.wlattr, query: request.data.wlpat, extra: ''}
                : (method === "extract_keywords") ? {attr: request.data.attr, query: request.data.wlpat, extra: ''}
                : null
            // filter pagesize 1000 / 1 for concordance (preload/final stats)
            let skip = (method === "concordance" && (request.data.pagesize === 1 || request.data.pagesize === 1000))
            console.debug("request: method=<", method, ">, corpus=<", corpus, ">, query=<", query, ">, data=", request.data)
            if (query && !skip) {
                _paq.push(['setCustomVariable', 1, 'Corpus', corpus, 'page'])
                _paq.push(['trackSiteSearch', query.query, `${corpus}:${method}${query.extra}`, false])
            }
        }

        let xhrParams = this._getXhrParams(request)

        let xhr = $.ajax(xhrParams)
            .done(this._onDone.bind(this, request))
            .fail(this._onFail.bind(this, request))
            .always(this._onAlways.bind(this, request));

        request.xhr = xhr

        this.activeRequests.push(request)

        return request
    }

    createUrl(url, query){
        return createGETURL(url, query)
    }

    abortRequest(request){
        request && request.xhr && request.xhr.abort()
    }

    download(request, format) {
        request.data.format = format
        let xhrParams = this._getXhrParams(request)
        if (xhrParams.method == 'POST') {
            var form = document.createElement("form");
            form.action = xhrParams.url
            form.method = "POST"
            form.target = "_blank"
            if (typeof xhrParams.data == "string" && xhrParams.data.indexOf('json=') == 0) {
                var input = document.createElement("textarea")
                input.name = 'json'
                input.value = decodeURIComponent(xhrParams.data.substring(5))
                form.appendChild(input)
            }
            else {
                for (var key in xhrParams.data) {
                    var input = document.createElement("textarea")
                    input.name = key
                    input.value = typeof xhrParams.data[key] === "object" ?
                            JSON.stringify(xhrParams.data[key]) :
                            xhrParams.data[key]
                    form.appendChild(input)
                }
            }
            var input = document.createElement('textarea')
            input.name = 'format'
            input.value = format
            form.appendChild(input)
            form.style.display = 'none'
            document.body.appendChild(form)
            form.submit()
            // remove form from DOM?
        }
        else {
            window.open(xhrParams.url + '&format=' + format, "_blank" + (new Date).getTime())
        }
    }

    _getXhrParams(request){
        // returns object with params for ajax request
        let xhrParams = request.xhrParams || {}
        let method = "GET"
        let data =  request.data || {}
        let postKeys = request.postKeys || []  // key always sent in POST data
        let getKeys = request.getKeys || []  // key always sent in query string
        let postData = {}
        let getData = {}
        let jsonData = {}
        getKeys.push("corpname", "bim_corpname", "ref_corpname")  //allways in URL. BigBrother uses corpnames in URL to authorize user
        if(this.bonitoNote && request.url.startsWith(window.config.URL_BONITO)){
            getData.note = this.bonitoNote
        }
        if(!request.xhrParams || $.isEmptyObject(request.xhrParams)){
            for(let key in data){
                let value = data[key]
                if(isDef(value)){
                    if(getKeys.includes(key)
                        || (!postKeys.includes(key)
                                && typeof value != "object"
                                && (JSON.stringify(value)).length <= this.MAX_QUERY_VALUE_LENGTH
                            )
                        ){
                        getData[key] = value
                    } else {
                        if(typeof value == "object"){
                            jsonData[key] = value
                        } else {
                            postData[key] = value
                        }
                    }
                }
            }
            if(!$.isEmptyObject(jsonData)){
                let jsonString = JSON.stringify(jsonData)
                if(jsonString.length <= this.MAX_QUERY_VALUE_LENGTH){
                    getData.json = jsonString
                } else {
                    postData.json = jsonString
                }
            }
            if(!$.isEmptyObject(postData)){
                if(method == "GET"){
                    method = "POST"
                }
                xhrParams.data = postData
            }
            xhrParams.method = method
            if(request.contentType){
                xhrParams.contentType = request.contentType
            }
        }

        xhrParams.url = xhrParams.url || createGETURL(request.url, getData)
        xhrParams.xhrFields = {withCredentials: true}
        xhrParams.crossDomain = true

        return xhrParams
    }

    _onDone(request, payload){
        this._checkNewBonitoVersion(request, payload)
        request.done && request.done(payload, request)
    }

    _onFail(request, payload){
        if(!request.skipDefaultCallbacks){
            if(request.xhr.statusText == "abort"){
                return
            }
            if(payload.status == 401){
                checkSessionAndRedirect(request, payload)
                return
            }
            if(payload.status == 403){
                checkSessionAndRedirect(request, payload, (authorized) => {
                    authorized && Dispatcher.trigger("ROUTER_GO_TO", "corpus")
                })
                return
            }
            if (payload.status == 504) {
                SkE.showError(_("err.responseTimeOut", ["<a id=\"openFeedbackLink\" class=\"link\">" + _("sendUsFeedback") + "</a>"]))
                delay(() => {$("#openFeedbackLink").click(() => {
                    Dispatcher.trigger("closeDialog")
                    Dispatcher.trigger('openDialog', {
                        tag: 'feedback-dialog',
                        title: _('fb.feedback'),
                        buttons: [{
                            label: _("send"),
                            class: "sendFeedbackBtn btn-primary",
                            onClick: (dialog) => {
                                dialog.contentTag.refs.feedback.send()
                            }
                        }]
                    })
                })}, 500) //  wait until dialog is open
            }
        }
        if(payload.status == 429){
            Dispatcher.trigger("FUPLimitReached")
            return
        }
        if(request.fail){
            request.fail(payload.responseJSON ? payload.responseJSON : payload, request);
        }
    }

    _onAlways(request, payload){
        this.activeRequests = this.activeRequests.filter(r => r != request)
        if(!this.activeRequests.length){
            Dispatcher.trigger("NO_ACTIVE_REQUEST")
        }
        if(request.xhr.statusText == "abort"){
            return
        }
        if(request.loadingId){
            Dispatcher.trigger("LOADING_CHANGED", false, request.loadingId);
        }
        if(request.always){
            request.always(payload, request);
        }
    }

    _checkNewBonitoVersion(request, payload){
        if(request.url && request.url.indexOf(window.config.URL_BONITO) != -1){
            let version = payload && payload.api_version || null
            if(version != this.lastBonitoVersion){
                if(this.lastBonitoVersion !== null){
                    window.appUpdater && window.appUpdater.checkNow()
                }
                this.lastBonitoVersion = version
            }
        }
    }
}

class SSEConnectionClass{

    get(request){
        if(request.loadingId){
            Dispatcher.trigger("LOADING_CHANGED", true, request.loadingId)
        }

        let url = createGETURL(request.url, request.data)

        const eventSource = new EventSource(url, { withCredentials: true } )
        eventSource.onmessage = this._onMessage.bind(this, request)
        eventSource.onerror = this._onFail.bind(this, request)

        request.eventSource = eventSource

        return request
    }

    abortRequest(request){
        request && request.eventSource && request.eventSource.close()
    }

    _onMessage(request, payload){
        request.message && request.message(JSON.parse(payload.data), request)
    }

    _onFail(request, payload){
        if(!request.skipDefaultCallbacks){
            if(payload.status == 401){
                checkSessionAndRedirect(request, payload)
                return
            }
            if(payload.status == 403){
                checkSessionAndRedirect(request, payload, (authorized) => {
                    authorized && Dispatcher.trigger("ROUTER_GO_TO", "corpus")
                })
                return
            }
            if (payload.status >= 500 && payload.status < 600) {
                SkE.showError(_(payload.status == 504 ? "err.responseTimeOut" : "err.unknowServerError", ["<a id=\"openFeedbackLink\" class=\"link\">" + _("sendUsFeedback") + "</a>"]))
                delay(() => {$("#openFeedbackLink").click(() => {
                    Dispatcher.trigger("closeDialog")
                    Dispatcher.trigger('openDialog', {
                        tag: 'feedback-dialog',
                        title: _('fb.feedback'),
                        buttons: [{
                            label: _("send"),
                            class: "sendFeedbackBtn btn-primary",
                            onClick: (dialog) => {
                                dialog.contentTag.refs.feedback.send()
                            }
                        }]
                    })
                })}, 500) //  wait until dialog is open
            }
        }
        if(payload.status == 429){
            Dispatcher.trigger("FUPLimitReached")
            return
        }
        if(request.fail){
            request.fail(payload.responseJSON ? payload.responseJSON : payload, request);
        }
        this.abortRequest(request)
    }
}

export let Connection = new ConnectionClass(), SSEConnection = new SSEConnectionClass();
