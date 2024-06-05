<wordlist-result-table class="wordlist-result-table">
    <div if={!data.isEmpty && !data.isEmptySearch}
            class={oneColumn: data.onecolumn}>
        <column-table ref="table"
            show-line-nums={data.showLineNumbers}
            items={data.showItems}
            col-meta={colMeta}
            sort="desc"
            order-by={data.wlsort}
            on-sort={onSort}
            max-column-count={data.onecolumn ? 1 : 0}
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
                generator: () => {
                    return "<a class=\"iconButton btn btn-flat btn-floating\"><i class=\"material-icons menuIcon\" >more_horiz</i></a>"
                },
                onclick: function(item, colMeta, evt){
                    this.refs.interfeatureMenu.onOpenMenuButtonClick(evt, item)
                }.bind(this)
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
                    tab: 'advanced',
                    queryselector: "cql",
                    default_attr: "word",
                    usesubcorp: options.usesubcorp,
                    tts: options.tts,
                    cql: cql
                }
            } else if(feature == "ngrams"){
                return {
                    tab: 'advanced',
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
                    tab: 'advanced',
                    lemma: lemma,
                    usesubcorp: options.usesubcorp,
                    tts: options.tts,
                    lpos: lpos
                }
            } else if(feature == "thesaurus"){
                return {
                    tab: 'advanced',
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
                        return '<div class="progress"><div class="determinate" style="width: ' + (item.fbar / 3) + '%;"></div></div>'
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

        this.on("update", this.setColMeta)
    </script>
</wordlist-result-table>
