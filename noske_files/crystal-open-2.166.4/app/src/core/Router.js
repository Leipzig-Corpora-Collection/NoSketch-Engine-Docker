const {RoutingMeta} = require('core/Meta/Routing.meta.js')
const {Auth} = require("core/Auth.js");
const {Url} = require("core/url.js");
const {AppStore} = require("core/AppStore.js")
import route from 'riot-route'

class RouterClass{
    constructor(){
        Dispatcher.on("SESSION_LOADED", this._onSessionLoaded.bind(this))
        Dispatcher.on("ROUTER_GO_TO", this.goTo.bind(this))
        Dispatcher.on("APP_READY_CHANGED", function(ready){
            ready && this._onAppReady()
        }.bind(this))
    }

    getActualPage(){
        return this._actualPage
    }

    getActualPageLabel(){
        let meta = this._getPageActualMeta()
        return meta ? getLabel(meta) : ""
    }

    getActualFeature(){
        // acording to actual page returns feature, to which page belongs (wordlist-result->wordlist)
        return this._getPageFeature(this._actualPage)
    }

    goTo(page, query){
        window.location.href = Url.create(page, query)
    }

    _initRouter(){
        route.create()
        route(this._onPageChange.bind(this))
        route.parser(function(path){
            let tmp = path.split("?")
            return [tmp[0], Url.parseQuery(tmp[1])]
        }.bind(this))
        route.start(false)
    }

    _onPageChange(pageId, queryObj){
        queryObj = queryObj || {}
        queryObj.note && Dispatcher.trigger("NOTE_CHANGED", queryObj.note)
        // user clicked on link, insert url address or navigate browser back/forward
        if(queryObj.corpname){
            const corpus = AppStore.getActualCorpus()
            if(!corpus || corpus.corpname != queryObj.corpname){
                // corpus is defined and its not actual corpus -> need to load new corpus
                AppStore.changeCorpus(queryObj.corpname)
                AppStore.one("corpusChanged", this._checkAndSetPage.bind(this, pageId, queryObj))
                return
            }
        }
        this._checkAndSetPage(pageId, queryObj)
    }

    _onSessionLoaded(payload){
        if(!Auth.isLogged()){
            if(window.config.URL_RASPI){
                window.location.href = window.config.URL_RASPI + "?next=" + encodeURIComponent(window.location.href)
            } else {
                Dispatcher.trigger("ROUTER_CHANGE", "unauthorized", {})
            }
        } else{
            this._initRouter()
        }
    }

    _checkAndSetPage(pageId, queryObj){
        let page = this._getPageToNaviagateTo(pageId, queryObj)
        let q = queryObj
        if(page != pageId){
            q = {}
        }
        let url = Url.create(page, q)
        // keep url and router state synchronized
        history.replaceState(null, null, url)
        route.base()
        this._actualPage = page
        this._setDocumentTitle()
        Dispatcher.trigger("ROUTER_CHANGE", this._actualPage, q)
    }

    _getPageToNaviagateTo(page, queryObj){
        // check, if navigation to desired page is allowed.
        // Otherwise return page to route to
        let isLogged = Auth.isLogged()
        let isFullAccount = Auth.isFullAccount()
        let isAnonymous = Auth.isAnonymous()
        let corpus = AppStore.getActualCorpus()
        let urlCorpus = Url.getQuery().corpname
        let pageFeature = this._getPageFeature(page)
        if(!window.config.NO_CA){ // in NO_CA mode user can access everything
            if(!isLogged
                || (isAnonymous && page != "open" && !corpus && !urlCorpus && page != "404" && page != "not-allowed")){
                window.location.href = window.config.URL_RASPI + "?next=" + encodeURIComponent(window.location.href)
            }
        }
        if(!RoutingMeta.table[page]){
            debugger
            page = RoutingMeta.notFound
        }
        if(isFullAccount){
            if(page == "open"){
                page = "corpus"
            }
        }
        if(isAnonymous){
            if(page == "corpus"){
                page = "open"
            }
        }
        if(isDef(window.permissions[page]) && !window.permissions[page]){
            page = "not-allowed"
        }
        if(this._pageNeedCorpus(page)){
            if(!corpus){
                delay(SkE.showToast.bind(null, _("msg.selectCorpusFirst")), 500)
                page = "corpus"
            } else{
                if(corpus.isCompiled){
                    if(pageFeature && !AppStore.hasCorpusFeature(pageFeature)){
                        delay(SkE.showToast.bind(null, _("msg.corpusHasNotThisFeature")), 500)
                        page = "dashboard"
                    }
                } else if(corpus.isReady){
                    delay(SkE.showToast.bind(null, _("msg.corpusNeedsCompile")), 500)
                    page = "ca-compile"
                } else if (corpus.isCompiling){
                    delay(SkE.showToast.bind(null, _("msg.corpusIsCompiling")), 500)
                    page = "ca-compile"
                } else if(corpus.isEmpty){
                    delay(SkE.showToast.bind(null, _("msg.corpusIsEmpty")), 500)
                    page = "dashboard"
                }
            }
        }
        return page
    }

    _onAppReady(){
        // user is logged and corpus is loaded (if there is specified corpus)
        this._initPage()
    }

    _pageNeedCorpus(pageId){
        // page is feature -> it needs corpus
        return !!this._getPageFeature(pageId)
    }

    _getPageActualMeta(){
        return RoutingMeta.table[this._actualPage]
    }

    _getPageFeature(pageId){
        let meta = RoutingMeta.table[pageId]
        return meta ? meta.feature : null
    }

    _initPage(){
        let corpus = AppStore.getActualCorpus()
        let page = Url.getPage() || (corpus ? "dashboard" : "corpus")
        this._checkAndSetPage(page, Url.getQuery())
    }

    _setDocumentTitle(){
        document.title =  [this.getActualPageLabel(), "Sketch Engine"].join(" | ")
    }
}

export let Router = new RouterClass()
