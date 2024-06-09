const {FeatureStoreMixin} = require("core/FeatureStoreMixin.js")
const {AppStore} = require("core/AppStore.js")
const {Connection, SSEConnection} = require('core/Connection.js')
const {Url} = require("core/url.js")
const Meta = require("./Wordlist.meta.js")

class WordlistStoreClass extends FeatureStoreMixin {
    constructor(){
        super()
        this.feature = "wordlist"
        this.data = $.extend(this.data, {
            onecolumn: false,
            bars: true,
            random: false,
            find: "word",
            lpos: "",
            filter: "all",
            keyword: "",
            viewAs: 1,
            cols: ["frq"],
            showLineNumbers: true,
            wlmaxitems: 20000,
            wlsort: "frq",
            usesubcorp: "",
            wlattr: "word",
            wlpat: ".*",
            wlminfreq: 5,
            wlmaxfreq: 0,
            wlfile: "",
            wlblacklist: "",
            wltype: "simple",
            wlstruct_attr1: "",
            wlstruct_attr2: "",
            wlstruct_attr3: "",
            wlicase: true,
            include_nonwords: false,
            criteria: [],
            exclude: false,
            criteriaOperator: Meta.operators.AND, // criteria joined with AND
            itemsPerPage: 50,
            histid: "",
            findxList: [],
            showrank: false,
            showratio: true,
            showtimelines: false,
            findxListLoaded: false,
            chartitems: 10,
            timelines: {},
            diaattr: "",
            showtimelineabs: false,
            timelinesthreshold: 5
        })
        this.defaults = window.copy(this.data)

        this.xhrOptions = ["wlmaxitems", "wlsort",
                "usesubcorp", "wlattr", "wlpat", "wlminfreq", "wlicase",
                "wlmaxfreq", "wlfile", "wlblacklist", "wlnums", "wltype", "include_nonwords",
                "wlstruct_attr1", "wlstruct_attr2", "wlstruct_attr3", "random"]

        this.urlOptions = ["lpos", "find", "keyword", "filter", "viewAs",
            "onecolumn", "bars", "wlmaxitems",
            "usesubcorp", "wlattr", "wlminfreq", "wlicase",
            "wlmaxfreq", "wlfile", "wlblacklist", "wltype", "exclude",
            "wlstruct_attr1", "wlstruct_attr2", "wlstruct_attr3", "criteria",
            "include_nonwords", "criteriaOperator", "page", "itemsPerPage",
            "showLineNumbers", "tab", "showresults", "random", "tts", "histid",
            "showrank", "showratio", "chartitems", "cols", "search_query",
            "search_mode", "search_matchCase", "showtimelines", "diaattr",
            "showtimelineabs", "timelinesthreshold"]

        this.searchOptions = [
            ["wlmaxitems", "maxItems"],
            ["usesubcorp", "subcorpus"],
            ["wlattr", "attribute"],
            ["wlpat", "wlpat"],
            ["wlminfreq", "minFreq"],
            ["wlmaxfreq", "maxFreq"],
            ["wlfile", "whitelist"],
            ["wlblacklist", "blacklist"],
            ["viewAs", "wl.viewResultAs"],
            ["wlstruct_attr1", "wlstruct_attr"],
            ["wlstruct_attr2", "wlstruct_attr"],
            ["wlstruct_attr3", "wlstruct_attr"],
            ["wlicase", "icase"],
            ["include_nonwords", "includeNonwords"],
            ["criteria", "criteria"],
            ["exclude", "wl.excludeWords"],
            ["criteriaOperator", "criteriaOperator"],
            ["random", "random"],
            ["histid", "histid"]
        ]

        this.userOptionsToSave = ["tab", "itemsPerPage", "cols", "diaattr", "showtimelineabs", "timelinesthreshold"]
    }

    search(){ //overrides default
        if(!this._isTextTypeAnalysis() && !this.data.histid){
            this.setWlattrAndLpos()
        }
        super.search()
    }

    onDataLoadedProcessItems(payload){ //overrides default
        this.data.items = payload.Blocks ? payload.Blocks[0].Items : payload.Items
        this.data.wllimit = payload.wllimit
        this.data.totalfrq = payload.totalfrq
        this.data.totalitems = payload.Blocks ? payload.Blocks[0].total : payload.total
    }

    onDataLoaded(payload){
        super.onDataLoaded(payload)
        if(!this._isTextTypeAnalysis()
                && this.data.wlminfreq > 1
                && this.data.raw.new_maxitems
                && this.data.raw.new_maxitems > this.data.items.length ){
            SkE.showToast(_("docfFreqWarning", [this.data.wlminfreq]), 8000)
        }
        this.loadTimelines()
    }

    changePage(page){
        super.changePage(page)
        this.loadTimelines()
    }

    changeItemsPerPage(itemsPerPage){
        super.changeItemsPerPage(itemsPerPage)
        this.loadTimelines()
    }

    changeShowtimelines(showtimelines){
        this.data.showtimelines = showtimelines
        this.updatePageTag()
        this.saveUserOptions(["showtimelines"])
        this.updateUrl(true)
        if(showtimelines){
            this.loadTimelines()
        } else{
            this.timelineRequest && this.timelineRequest.eventSource.close()
            this.data.timelines = []
        }
    }

    changeTimelinesthreshold(timelinesthreshold){
        this.data.timelinesthreshold = timelinesthreshold
        this.data.timelines = []
        this.saveUserOptions(["timelinesthreshold"])
        this.updateUrl(true)
        this.loadTimelines()
    }

    changeDiaattr(diaattr){
        this.data.diaattr = diaattr
        this.data.timelines = []
        this.saveUserOptions(["diaattr"])
        this.updateUrl(true)
        this.loadTimelines()
        this.updatePageTag()
    }

    changeShowtimelineabs(showtimelineabs){
        this.data.showtimelineabs = showtimelineabs
        this.saveUserOptions(["showtimelineabs"])
        this.updateUrl(true)
        this.updatePageTag()
    }

    loadTimelines(){
        if(this.data.showtimelines && !this.data.wlstruct_attr1 && !this._isTextTypeAnalysis()){
            Object.values(this.data.timelines).forEach(word => {
                delete word.isLoading
            })
            this.timelineRequest && this.timelineRequest.eventSource.close()
            this.timelineRequest = null
            this.timelineWordsToLoad = []
            this.data.showItems.forEach(item => {
                let word = item.str
                if(!this.data.timelines[word]){
                    this.data.timelines[word] = {}
                }
                if(!this.data.timelines[word].data){
                    this.timelineWordsToLoad.push(window.escapeRE(word))
                    this.data.timelines[word].isLoading = true
                    this.data.timelines[word].random = item.frq > 10000000
                }
            })
            this.trigger("TIMELINE_LOADING_STARTED")
            this.loadNextTimelineBatch()
        }
    }

    loadNextTimelineBatch(){
        // split request to batches of up to 100 words so request URL is not too long and it wont be rejected
        if(this.timelineWordsToLoad.length){
            let wlattr = this.data.lpos ? (this.data.wlicase ? "lc" : "word") : this.data.wlattr
            this.timelineRequest = SSEConnection.get({
                url: window.config.URL_BONITO + "freqdist",
                data: {
                    corpname: this.corpus.corpname,
                    ctx: "0~0>0",
                    diaattr: this.data.diaattr,
                    wlattr: wlattr,
                    sse: 1,
                    threshold: this.data.timelinesthreshold / 100,
                    json: JSON.stringify({
                        wordlist: this.timelineWordsToLoad.splice(0, 100)
                    })
                },
                message: function(wlattr, payload){
                    if(payload.finish){
                        this.timelineRequest.eventSource.close()
                        this.loadNextTimelineBatch()
                    } else {
                        let word = payload[wlattr].replaceAll("\\", "")
                        if(payload.error){
                            console.log(`Could not load timelines:`, payload.error)
                            this.data.timelines[word].data = []
                        } else {
                            if(this.data.timelines[word]){
                                let data = Object.entries(Object.assign({}, payload.freqdist, payload.removed_freqdist)).filter(item => {
                                    return item[0] != "===NONE===" && item[0] != ""
                                }).map(item => {
                                    if(payload.removed_freqdist[item[0]]){
                                        return {  // items under threshold, do not show lines in this period in chart
                                            w: item[0],
                                            frq: null,
                                            rel_frq: null
                                        }
                                    } else {
                                        return {
                                            w: item[0],
                                            frq: item[1].frq,
                                            rel_frq: item[1].rel_frq
                                        }
                                    }
                                })
                                data.sort((a, b) => {
                                   return a.w < b.w ? -1 : 1
                                })
                                this.data.timelines[word].data = data
                            }
                        }
                        this.data.timelines[word].isLoading = false
                        this.trigger("TIMELINE_LOADED", word)
                    }
                }.bind(this, wlattr),
                fail: payload => {
                    console.log(`Could not load timelines:`, getPayloadError(payload))
                }
            })
        }
    }

    loadFindxList(){
        if(!this.data.findxListLoaded){
            Connection.get({
                url: window.config.URL_BONITO + "findx_list",
                data: {
                    corpname: this.corpus.corpname
                },
                done: (payload) => {
                    this.data.findxListLoaded = true
                    this.data.findxList = payload.FindxList || []
                    this.trigger("findxListLoaded")
                }
            })
        }
    }

    filterTestItem(re, item){
        if(this.isStructuredWordlist()){
            return item.Word.some(word => re.test(word.n))
        } else if(this.data.histid){
            return re.test(item.word)
        } else {
            return re.test(item.str)
        }
    }

    saveUserOptions(userOptionsToSave){ //overrides default
        !this._isTextTypeAnalysis() && super.saveUserOptions(userOptionsToSave || this.userOptionsToSave)
    }

    setCorpusDefaults(){ //overrides default
        let attr = AppStore.getAttributeByName("word")
        if(this.corpus){
            if(this.corpus.unicameral){
                this.data.wlicase = false
            }
            this.data.showtimelines = this.corpus.diachronic.length
            this.data.diaattr = this.corpus.diachronic.length ? this.corpus.diachronic[0].value : ""
        }
        if(attr){
            if(!attr.lc){
                this.data.wlicase = false
            } else{
                this.data.wlattr = this.data.wlicase ? attr.lc : attr.name
            }
        }
        if(!isDef(this.userOptions.wlminfreq) && (this.corpus.sizes.tokencount * 1 < 10000000)){
            this.data.wlminfreq = 0
        }
    }

    getDefaultPosAttribute(){
        let attribute = AppStore.getAttributeByName("lempos")
            || AppStore.getAttributeByName("wordpos")
            || AppStore.getAttributeByName("stempos")
        return attribute ? attribute.name : ""
    }

    setWlattrAndLpos(){
        let attrName = this.data.find
        if(AppStore.getLposByValue(this.data.find)){
            attrName = this.getDefaultPosAttribute()
            this.data.lpos = this.data.find
        } else {
            this.data.lpos = ""
        }
        let attr = AppStore.getAttributeByName(attrName)
        this.data.wlattr = this.data.wlicase && attr.lc ? attr.lc : attrName
    }

    getFilterList(tab){
        return Meta.filterList[tab].map((filter) => {
            return Object.assign({}, Meta.filters[filter])
        })
    }

    getUserOptions(){
        const addValueToList = (isDefault, key, labelId, value) => {
            if(!isDefault){
                userOptions.push({
                    key: key,
                    labelId: labelId,
                    value: value
                })
            }
        }
        let value
        let userOptions = []
        let options = this.data
        addValueToList(false, "find",  "show",  options.find)

        if(options.filter == "all"){
            //
        } else if(options.filter === ""){
            if(!options.criteria.length){
                addValueToList(true, "filter", "filter", options.keyword)
            }
        } else {
            let filterMeta = Meta.filters[options.filter]
            let fromList = options.filter == "fromList" ? options.wlfile : options.keyword
            addValueToList(false, "fromList", filterMeta.labelId, fromList)
        }

        if(options.criteria.length){
            options.criteria.forEach((criterion) => {
                addValueToList(false, criterion.filter, Meta.filters[criterion.filter].labelId, criterion.value)
            })
        }
        if(options.wlblacklist){
            addValueToList(false, "notFromList", "wl.notFromList", options.wlblacklist)
        }
        this._addTextTypesToUserOptions(userOptions)
        ;[
            ["usesubcorp", "subcorpus"],
            ["wlminfreq", "minFreq"],
            ["wlmaxfreq", "maxFreq"],
            ["wlicase", "ignoreCase"],
            ["include_nonwords", "includeNonwords"],
            ["wlattr", "attribute"],
            ["wlstruct_attr1", "wlstruct_attr"],
            ["wlstruct_attr2", "wlstruct_attr"],
            ["wlstruct_attr3", "wlstruct_attr"],
            ["random", "randomSample"]

        ].forEach((option) => {
            value = options[option[0]]
            addValueToList(this.isOptionDefault(option[0], value), option[0], option[1], value)
        })
        return userOptions
    }

    getRequestUrl(){ // overrides default
        let method = "wordlist"
        if(this.data.histid){
            method = "findx"
        } else if(this.data.wlstruct_attr1){
            method = "struct_wordlist"
        } else if(this.data.lpos){
            method = "poswordlist"
        }
        return window.config.URL_BONITO + method
    }

    getRequestData(){ //overrides default
        let data = {}
        if(!this.data.histid){
            data = super.getRequestData()
            data.relfreq = 1
            data.reldocf = !this._isTextTypeAnalysis()
            data.wltype = "simple"
            if(this._isTextTypeAnalysis()){
                data.wlnums = ""
                data.include_nonwords = true
            } else {
                let cols = this.getRequestCols()
                data.wlnums = cols.join(",")
                if(this.data.wlblacklist && this.data.lpos){
                    // adding lpos to words in blacklist
                    data.wlblacklist = this.data.wlblacklist.split("\n").map(word => {
                        return word + this.data.lpos
                    }).join("\n")
                }
                if(this.data.wlstruct_attr1){
                    data.wltype = "struct_wordlist"
                    data.fmaxitems = this.data.wlmaxitems
                    data.wlnums = "frq"
                }
            }
            data[this.data.wltype == "struct_wordlist" ? "fpage" : "wlpage"] = 1
            data.wlpat = this.getWlpat()

        } else {
            data.corpname = this.corpus.corpname
            data.histid = this.data.find
            data.wlminfreq = this.data.wlminfreq
            data.wlmaxitems = this.data.wlmaxitems
            data.results_url = window.location.href + '&showresults=1'
        }
        data.wlfile = this._getWlfile()

        return data
    }

    getSearchOptions(){
        return {
            contentType: "application/x-www-form-urlencoded"
        }
    }

    getWlpat(){
        let options = this.data
        let criteria = window.copy(options.criteria) || [];
        if(options.filter){ // value from list All, Starting with,....
            if(options.filter != "fromList" && (options.filter == "all" || options.keyword !== "")){
                // whitelist doesnt change wlpat, other options than all have to have filled keyword
                criteria.push({
                    filter: options.filter,
                    value: options.keyword
                })
            }
        }
        let wlpat = ""
        let regex
        let joinWith = options.criteriaOperator == Meta.operators.OR ? "|" : ""
        // conditions to regex have to be added in specific order. Eg. startign with k and ending with a is (k.*)(.*a), not (.*a)(k.*)
        ;["startingWith", "containing", "endingWith", "regex"].forEach((filter) => {
            regex = this._getFilterRegex(criteria, filter)
            if(regex){
                wlpat += (wlpat ? joinWith : "") + regex
            }
        })

        if(!wlpat) {
            wlpat = this.defaults.wlpat
        }
        let lpos = AppStore.getLposByValue(options.find)
        if(lpos){
            wlpat += lpos.value // add lempos to wlpat -N, -j,...
        }

        return wlpat
    }

    getResultPageObject(){
        let resultObject = super.getResultPageObject()
        if(this._isTextTypeAnalysis()){
            resultObject.data.tta = 1
        }
        return resultObject
    }

    getUrlToResultPage(options){
        let data = Object.assign({showresults: 1}, options)
        return Url.create(data.tta ? "text-type-analysis" : this.feature, this._getQueryObject(data))
    }

    getDownloadRequest(idx){
        let request = super.getDownloadRequest(idx)
        let data = {
            relfreq: this.data.cols.includes("relfreq"),
            reldocf: this.data.cols.includes("reldocf"),
            wlmaxitems: this.data.wllimit || 10000000, // 0 means unlimited
            page: 1
        }
        if(!this.data.wlstruct_attr1){
            let cols = this.getRequestCols()
            data.wlnums = cols.join(",")
        }
        Object.assign(request.data, data)
        return request
    }

    getRequestCols(){
        let cols = this.data.cols.map(c => {
            c = c.startsWith("rel") ? c.substr(3) : c
            return c == "freq" ? "frq" : c
        }).filter(c => c != this.data.wlsort)
        return [...new Set(cols)] //remove duplicates
    }

    sortCols(){
        this.data.cols.sort((a, b) => {
            let idxA = Meta.wlnumsList.findIndex(i => i.value == a)
            if(idxA == -1){
                return 1
            }
            let idxB = Meta.wlnumsList.findIndex(i => i.value == b)
            if(idxB == -1){
                return -1
            }
            return idxA - idxB
        })
    }

    isStructuredWordlist(){
        return this.data.tab == "advanced" && this.data.viewAs == 2
    }

    getValueLabel(value, option){
        if(option == "find"){
            if(this._isTextTypeAnalysis()){
                return value
            } else if(this.data.histid){
                return this.data.raw && this.data.raw.hist_desc || ""
            } else {
                let attr = AppStore.getAttributeByName(value) || AppStore.getLposByValue(value)
                return attr ? attr.label : value
            }
        } else if(option == "wlattr"){
            return this.corpus.attributes.find(a => a.name == value).label
        } else if(option == "criteria"){
            return value.map(v => {
                return `${_(v.filter)} "${v.value}"`
            }).join(", ")
        } else if(option == "criteriaOperator"){
            return `"${this.data.criteriaOperator == 1 ? _("and") : _("or")}"`
        }
        return super.getValueLabel(value, option)
    }

    changeFilter(search_query, search_mode, search_matchCase){
        super.changeFilter(search_query, search_mode, search_matchCase)
        this.loadTimelines()
    }

    cancelFilter(){
        super.cancelFilter()
        this.loadTimelines()
    }

    _setDataFromUrl(query){
        // TODO just for temporary backwards compatibility, remove at the end of 2022
        super._setDataFromUrl(query)
        if(this.data.wlsort == "norm:l"){
            this.data.wlsort = "frq"
        }
    }

    _onPageChange(pageId, query){
        super._onPageChange(pageId, query)
        this.timelineRequest && this.timelineRequest.eventSource.close()
    }

    _onCorpusChange(){ // overrides default
        super._onCorpusChange()
        if(this._isActualFeature()){
            this.findxListLoaded = false
            this.loadFindxList()
            this.timelineRequest && this.timelineRequest.eventSource.close()
        }
    }

    _getQueryObject(data){ // overrides default
        let queryObject = super._getQueryObject(data)
        if(this._isTextTypeAnalysis()){
            queryObject.wlsort = this.data.wlsort
        }
        return queryObject
    }

    _getWlfile(){
        if(!this.data.wlfile){
            return ""
        }
        if(!this.data.lpos){
            return this.data.wlfile
        }
        // add lpos to wlfile
        return this.data.wlfile.split("\n").map(part => {
            part = part.trim()
            if(!part.endsWith(this.data.lpos)){
                part = part += this.data.lpos
            }
            return part
        }, this).join("\n")
    }

    _getFilterRegex(criteria, filter){
        let criterion = criteria.find((c) => {
            return c.filter == filter
        })
        if(!criterion){
            return ""
        }
        let filterMeta = Meta.filters[criterion.filter]
        return criterion.value ? `(${filterMeta.regex.replace("{key}", criterion.value)})` : filterMeta.regex
    }

    _isTextTypeAnalysis(){
        return window.location.href.split("?")[0].split("#")[1] == "text-type-analysis"
    }
}

export let WordlistStore = new WordlistStoreClass()
