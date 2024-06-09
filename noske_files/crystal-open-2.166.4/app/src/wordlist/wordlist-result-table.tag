<wordlist-result-table class="wordlist-result-table">
    <div if={!data.isEmpty && !data.isEmptySearch}
            class={oneColumn: data.onecolumn || data.showtimelines}>
        <column-table ref="table"
            show-line-nums={data.showLineNumbers}
            items={data.showItems}
            col-meta={colMeta}
            sort="desc"
            order-by={data.wlsort}
            on-sort={onSort}
            max-column-count={data.onecolumn || data.showtimelines ? 1 : 0}
            start-index={data.showResultsFrom}></column-table>

            <div class="row">
                <div class="inline-block left">
                    <user-limit wllimit={data.wllimit}
                            total={data.raw.total}
                            screen-limit={data.wlmaxitems}></user-limit>
                </div>
                <div class="inline-block right">
                    <ui-pagination
                        if={data.items.length > 10}
                        count={data.items.length}
                        items-per-page={data.itemsPerPage}
                        actual={data.page}
                        on-change={store.changePage.bind(store)}
                        on-items-per-page-change={store.changeItemsPerPage.bind(store)}
                        show-prev-next={true}></ui-pagination>
                </div>
            </div>

            <interfeature-menu ref="interfeatureMenu"
                features={interfeatureMenuFeatures}
                is-Feature-link-active={isFeatureLinkActive}
                get-feature-link-params={getFeatureLinkParams}></interfeature-menu>
        </div>

    <script>
        require("./wordlist-result-table.scss")
        const Meta = require("./Wordlist.meta.js")
        const {AppStore} = require("core/AppStore.js")
        const {UserDataStore} = require("core/UserDataStore.js")

        this.mixin("feature-child")

        this.interfeatureMenuFeatures = window.config.NO_SKE ? ["concordance", "concordanceMacro"] : ["concordance", "concordanceMacro", "ngrams", "wordsketch", "thesaurus"]

        onDownloadWordlistClick(){
            window.scrollTo(0, 0)
            Dispatcher.trigger("FEATURE_TOOLBAR_SHOW_OPTIONS", "download")
        }

        addMenuColumn(){
            this.colMeta.push({
                id: "menu",
                "class": "menuColumn col-tab-menu",
                label: "",
                generator: (item, cm) => {
                    let ret = ""
                    if(this.corpus.diachronic.length && this.data.showtimelines){
                        ret += `<a href="${this.getFreqDistLink(item)}"
                                        class="btn btn-floating btn-flat tooltipped"
                                        data-tooltip="${_("timelineData")}">
                                    <i class="material-icons rotate90CW timelineLink">insert_chart</i>
                                </a>`
                    }
                    return ret + `<a class=\"iconButton btn btn-flat btn-floating\">
                                        <i class=\"material-icons menuIcon\">more_horiz</i>
                                  </a>`
                },
                onclick: function(item, colMeta, evt){
                    if(!evt.target.classList.contains("timelineLink")){
                        this.refs.interfeatureMenu.onOpenMenuButtonClick(evt, item)
                    }
                }.bind(this)
            })
        }

        getFreqDistLink(item){
            let linkParams = this.getFeatureLinkParams("concordance", item)
            return window.stores.concordance.getUrlToResultPage(Object.assign(linkParams, {
                results_screen: "frequency",
                random: 1,
                f_freqml: [{
                    "attr": this.data.diaattr,
                    "ctx": "0",
                    "base": "kwic"
                }],
                f_sort: 0,
                f_tab: "advanced",
                t_attr: this.data.diaattr
            }))
        }

        addTimelineColumn(){
            this.corpus.diachronic.length && this.data.showtimelines && this.colMeta.push({
                id:"chart",
                class: "timeline chartPlaceholder",
                label: _("timeline"),
                tooltip: "t_id:timelines"
            })
        }

        getFeatureLinkParams(feature, item, evt, linkObj){
            let options = this.data
            let attr, lemma, lpos
            if(this.data.histid){
                let idx = item.word.lastIndexOf("-")
                lemma = item.word.substr(0, idx)
                lpos = item.word.substr(idx)
                attr = "lempos"
            } else {
                attr = options.viewAs == 1 ? options.find : options.wlstruct_attr1
                lpos = this.data.lpos ? this.data.lpos : ""
                lemma = isDef(item.str) ? item.str : item.Word[0].n
                if(attr == "lempos"){
                    let idx = lemma.lastIndexOf("-")
                    if(idx != -1){
                        lpos = lemma.substr(idx)
                        lemma = lemma.substr(0, idx)
                    }
                }
            }
            if(feature == "concordance"){
                let cql
                if(this.data.histid){
                    cql = `[lempos=="${item.word}"]`
                } else {
                    cql = ""
                    let attrs = ""
                    let esc = window.escapeCharacters
                    let specChars = '"\\'
                    if(item.Word){
                        if(options.wlstruct_attr1 != options.wlattr
                                    && options.wlstruct_attr2 != options.wlattr
                                    && options.wlstruct_attr3 != options.wlattr){
                            // add wlattr if its not in showed columns
                            attrs = `${options.wlattr}="${this.store.getWlpat()}"`
                        }
                        item.Word.forEach((w, i) => {
                            attrs += attrs ? " & " : ""
                            attrs += `${options["wlstruct_attr" + (i + 1)]}=="${esc(w.n,specChars)}"`
                        })
                    } else{
                        attrs = `${options.wlattr}=="${esc(item.str,specChars)}${esc(options.lpos,specChars)}"`
                    }
                    cql = `[${attrs}]`
                }
                return {
                    tab: "advanced",
                    queryselector: "cql",
                    default_attr: "word",
                    usesubcorp: options.usesubcorp,
                    tts: options.tts,
                    cql: cql
                }
            } else if(feature == "ngrams"){
                return {
                    tab: "advanced",
                    find: attr,
                    ngrams_n: 2,
                    ngrams_max_n: 6,
                    usesubcorp: options.usesubcorp,
                    tts: options.tts,
                    criteria: [{
                        filter: "containingWord",
                        value: lemma
                    }]
                }
            } else if(feature == "wordsketch"){
                return {
                    tab: "advanced",
                    lemma: lemma,
                    usesubcorp: options.usesubcorp,
                    tts: options.tts,
                    lpos: lpos
                }
            } else if(feature == "thesaurus"){
                return {
                    tab: "advanced",
                    lemma: lemma,
                    lpos: lpos
                }
            }
        }

        setColMetaSimple(){
            this.colMeta = [{
                id: "str",
                label: this.store.getValueLabel(this.data.find, "find"),
                "class": "_t word"
            }]
            this.data.cols.forEach(attr => {
                let labelId = AppStore.getWlsortLabelId(attr)
                let orderBy = attr.startsWith("rel") ? attr.substr(3) : attr
                if(orderBy == "freq"){
                    orderBy = "frq"
                }
                this.colMeta.push({
                    id: attr,
                    class: attr,
                    labelId: labelId,
                    num: true,
                    sort: {
                        orderBy: orderBy,
                        ascAllowed: true,
                        descAllowed: false
                    },
                    formatter: window.attrFormatter.bind(this, attr),
                    tooltip: "t_id:" + labelId
                })
            })
            this.addTimelineColumn()
            this.addMenuColumn()
        }

        setColMetaFindx(){
            let formatter = (digits, num) => {
                return window.Formatter.num(num, {maximumFractionDigits: digits})
            }
            this.colMeta = [{
                id: "word",
                label: this.data.raw && this.data.raw.wsattr ? _(this.data.raw.wsattr.split("_")[0]) : "",
                "class": "_t word"
            }]
            this.colMeta.push({
                id: "frq",
                class: "frq",
                label: _("frequency"),
                num: true,
                formatter: window.Formatter.num.bind(Formatter),
                tooltip: "t_id:frequency"
            })
            if(this.data.showratio){
                this.colMeta.push({
                    id: "ratio",
                    class: "ratio",
                    label: _("ratio"),
                    num: true,
                    formatter: formatter.bind(this, 4),
                    tooltip: "t_id:wl_r_ratio"
                })
            }
            if(this.data.showrank){
                this.colMeta.push({
                    id: "rank",
                    class: "rank addPercSuffix",
                    label: _("rank"),
                    num: true,
                    formatter: val => {return formatter(5, val * 100)},
                    tooltip: "t_id:wl_r_percentile"
                })
            }
            this.addMenuColumn()
        }

        setColMetaStructWordlist(){
            const cols = stores.wordlist.data.raw.Blocks ? stores.wordlist.data.raw.Blocks[0].Head : []
            cols.forEach((col) => {
                if(typeof col.s == "number"){
                    this.colMeta.push({
                        id: col.s,
                        class: $.escapeSelector(col.n.trim()),
                        label: col.n,
                        selector: (item, colMeta) => {
                            return item.Word[colMeta.id].n
                        }
                    })
                }
            })
            // column with frequencies
            if(this.data.cols.includes("frq")){
                this.colMeta.push({
                    id: "frq",
                    class: "frq",
                    label: this.countLabel,
                    num: true,
                    formatter: window.Formatter.num.bind(Formatter)
                })
            }

            // column with bars
            if(this.data.bars){
                this.colMeta.push({
                    "id": "frq",
                    "label": "",
                    "class": "barsColumn",
                    "generator": function(item, colMeta) {
                        return `<div class="progress"><div class="determinate" style="width: ${(item.fbar / 3)}%;"></div></div>`
                    }.bind(this)
                })
            }

            if (this.data.raw.concsize == this.data.raw.fullsize && this.data.cols.includes("relfreq")) {
                this.colMeta.push({
                    id: "fpm",
                    labelId: "relfreq",
                    class: "fpm",
                    formatter: window.Formatter.num.bind(Formatter),
                    num: true
                })
            }
            this.addMenuColumn()
        }

        setColMeta(){
            this.colMeta = []
            if (this.data.histid){
                this.countLabel = this.data.raw.hist_desc
                this.setColMetaFindx()
            } else {
                this.countLabel = getLabel(Meta.wlnumsList.find(w => {
                    return w.value == this.data.wlsort
                }))
                if(this.data.wlstruct_attr1){
                    this.setColMetaStructWordlist()
                } else{
                    this.setColMetaSimple()
                }
            }
        }
        this.setColMeta()

        onSort(sort){
            this.store.searchAndAddToHistory({
                wlsort: sort.orderBy
            })
        }

        isFeatureLinkActive(feature){
            let attr = this.data.viewAs == 1 ? this.data.wlattr : this.data.wlstruct_attr1
            if(feature == "concordance"){
                return true
            } else if(feature == "ngrams"){
                return attr == "word" || attr == "lc" || attr == "tag"
            } else { // thesaurus, wordsketch
                return attr == "word" || attr == "lc" || attr == "lemma"
                        || attr == "lemma_lc" || attr == "lempos" || attr == "lempos_lc"
            }
        }

        initAllCharts(){
            this.data.showItems.forEach(item => {
                this.queueChartInitilization(item.str)
            })
        }

        onTimelineLoading(){
            let displayedWords = this.data.showItems.map(item => item.str)
            Object.entries(this.data.timelines).forEach(obj => {
                let word = obj[0]
                let idx = displayedWords.indexOf(word)
                if(idx != -1 && obj[1].isLoading){
                    let element = $(`.column-table tbody tr:nth-child(${idx+1}) .timeline`)
                    if(element.length){
                        element.empty()
                        element.removeClass("noData")
                        element.addClass("chartPlaceholder")
                    }
                }
            })
        }

        queueChartInitilization(word){
            if(!this.chartInitializationQueue.includes(word)){
                this.chartInitializationQueue.push(word)
            }
            this.initNextChart()
        }

        initNextChart(){
            if(!AppStore.isGoogleChartsLoaded
                    || !this.chartInitializationQueue.length
                    || this.chartInitializationInProgress){
                return
            }
            let word = this.chartInitializationQueue.shift()
            let idx = this.data.showItems.map(item => item.str).indexOf(word)
            if(idx != -1){
                if(this.data.timelines[word]){
                    let data = this.data.timelines[word].data
                    if(data){
                        let element = $(`.column-table tbody tr:nth-child(${idx+1}) .timeline`)[0]
                        if(element && !element.childElementCount){
                            if(data.length){
                                this.initChart(word, element)
                            } else {
                                element.classList.add("noData")
                            }
                        }
                    }
                }
            }
            this.initNextChart()
        }

        initChart(word, element){
            var dataTable = new google.visualization.DataTable()
            dataTable.addColumn("string", _("period"))
            dataTable.addColumn("number", _("relativeFrequency"))
            dataTable.addColumn("number", ":" + _("noData"))
            dataTable.addColumn({type: "string", role: "tooltip"});
            this.data.showtimelineabs && dataTable.addColumn("number", _("absoluteFrequency"))
            dataTable.addRows(this.getChartData(word))

            var options = {
                allowAsync: true,
                height: 170,
                width: 600,
                chartArea: {
                    left: 60,
                    right: this.data.showtimelineabs ? 80 : 20,
                    bottom: 50,
                    top: 20,
                    width: "80%",
                    height: "80%"
                },
                hAxis: {
                    gridlineColor: "transparent",
                    textStyle: {
                        fontSize: 12,
                        color: "#808080"
                    }
                },
                vAxis:{
                    baseline: 0,
                    baselineColor: "transparent",
                    textStyle: {
                        fontSize: 12,
                        color: "#808080"
                    }
                },
                vAxes: [{
                    minValue: 0
                }],
                focusTarget: "category",
                backgroundColor: {
                    fill:"transparent"
                },
                legend: {
                    position: "none"
                }
            }
            options.series = {
                0: {
                    targetAxisIndex: 0,
                    type: "line"
                },
                1: {
                    targetAxisIndex: 0,
                    type: "line",
                    color: "dc3912"
                }
            }

            if(this.data.showtimelineabs){
                options.series[2] = {
                    targetAxisIndex: 1,
                    type: "bars",
                    color: "cccccc"
                }
                options.vAxes[0].title = _("relativeFrequency")
                options.vAxes.push({
                    title: _("absoluteFrequency"),
                    minValue: 0
                })
            }

            this.chartInitializationInProgress = true
            var chart = new google.visualization.ComboChart(element)
            google.visualization.events.addListener(chart, "ready", this.onChartInitialized.bind(this))
            chart.draw(dataTable, options)
            element.classList.remove("chartPlaceholder")
            if(this.data.timelines[word].random){
                let warningIcon = $(`<span class="btn btn-floating btn-tiny red tooltipped right cursor-default" data-tooltip="${_("timeline10MWarning")}"><i class="material-icons">priority_high</i><span>`)
                $(element).prepend(warningIcon)
                warningIcon.tooltip()
            }
        }

        getChartData(word){
            return this.data.timelines[word].data.map(item => {
                let noData = item.frq == null ? 0 : null
                if(this.data.showtimelineabs){
                    return [item.w, item.rel_frq, noData, noData === null ? "" : " ", item.frq]
                } else {
                    return [item.w, item.rel_frq, noData, noData === null? "" : " "]
                }
            })
        }

        onChartInitialized(){
            setTimeout(() => {
                this.chartInitializationInProgress = false
                this.initNextChart()
            }, 20)  // so browser wont freeze if too many charts are rendered
        }

        this.on("mount", () => {
            AppStore.loadGoogleCharts()
            this.chartInitializationQueue = []
            this.initAllCharts()
            this.store.on("TIMELINE_LOADED", this.queueChartInitilization)
            this.store.on("TIMELINE_LOADING_STARTED", this.onTimelineLoading)
            AppStore.on("GOOGLE_CHARTS_LOADED", this.initAllCharts)
        })
        this.on("before-unmount", () => {
            this.store.off("TIMELINE_LOADED", this.queueChartInitilization)
            this.store.off("TIMELINE_LOADING_STARTED", this.onTimelineLoading)
            AppStore.off("GOOGLE_CHARTS_LOADED", this.initAllCharts)
        })
        this.on("update", this.setColMeta)
        this.on("updated", this.initAllCharts)

    </script>
</wordlist-result-table>
