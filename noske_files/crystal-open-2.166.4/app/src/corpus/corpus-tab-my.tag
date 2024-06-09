<corpus-tab-my class="corpus-tab-my">
    <preloader-spinner if={!corpusListLoaded} center=1></preloader-spinner>
    <div class="tab-content card-content">
        <div class="controlBar mb-4">
            <ui-input riot-value={searchQuery}
                    class="fuzzy-input"
                    placeholder={_("cp.filterByName")}
                    inline={true}
                    size=15
                    ref="filter"
                    floating-dropdown={true}
                    on-input={onQueryChangeDebounced}
                    suffix-icon={searchQuery !== "" ? "close" : "search"}
                    on-suffix-icon-click={onSuffixIconClick}>
            </ui-input>
            <a href="#ca-create" if={window.permissions["ca-create"]}
                    class="btn btn-primary tooltipped btnNewCorpus"
                    data-tooltip={_("ca.newCorpusDesc")}>
                {_("newCorpus")}
            </a>
        </div>
        <table if={corpusListLoaded} class="table material-table highlight myseltab">
            <thead>
                <tr>
                    <th class="sc-lang">
                        <table-label
                            label={_("language")}
                            desc-allowed={true}
                            asc-allowed={true}
                            order-by="lang"
                            actual-sort={sort.sort}
                            actual-order-by={sort.orderBy}
                            on-sort={onSort}>
                        </table-label>
                    </th>
                    <th>
                        <table-label
                            label={_("name")}
                            desc-allowed={true}
                            asc-allowed={true}
                            order-by="name"
                            actual-sort={sort.sort}
                            actual-order-by={sort.orderBy}
                            on-sort={onSort}>
                        </table-label>
                    </th>
                    <th class="sc-size">
                        <table-label
                            align-right=1
                            label={_("wordP")}
                            desc-allowed={true}
                            asc-allowed={true}
                            order-by="size"
                            actual-sort={sort.sort}
                            actual-order-by={sort.orderBy}
                            on-sort={onSort}>
                        </table-label>
                    </th>
                    <th class="sc-size">
                        <table-label
                            align-right=1
                            label={_("sentences")}
                            desc-allowed={true}
                            asc-allowed={true}
                            order-by="sizeS"
                            actual-sort={sort.sort}
                            actual-order-by={sort.orderBy}
                            on-sort={onSort}>
                        </table-label>
                    </th>
                    <th style="width: 1px;"></th>
                </tr>
            </thead>
            <tbody if={!visibleCorpora.length}>
                <tr>
                    <td colspan="4">{_("cp.emptyList")}</td>
                </tr>
            </tbody>
            <tbody if={visibleCorpora.length}>
                <tr class="{actual: corpus.corpname == actCorp} row_{idx}"
                        each={corpus, idx in visibleCorpora}
                        if={idx < showLimit }
                        ref="{idx}_r">
                    <td onclick={onSelectCorpus} ref="{idx}_l">{corpus.language_name}</td>
                    <td onclick={onSelectCorpus}>
                        <i class="material-icons shared tooltipped" data-tooltip={_("iShareCorpus")} if={corpus.is_shared}>group</i>
                        <span ref="{idx}_n">{corpus.name}</span>
                        <span class="badge new background-color-blue-100 hide-on-small-and-down"
                            if={corpus.owner_name && corpus.owner_name != username}
                            data-badge-caption="">
                            {corpus.owner_name}
                        </span>
                    </td>
                    <td onclick={onSelectCorpus} class="right-align">
                        {corpus.sizes ? window.Formatter.num(corpus.sizes.wordcount) : ""}
                    </td>
                    <td onclick={onSelectCorpus} class="right-align">
                        {corpus.sizes && window.Formatter.num(corpus.sizes.sentcount) || ''}
                    </td>
                    <td class="menuCell relative">
                        <a href="javascript:void(0);"
                                if={!config.READ_ONLY}
                                class="iconButton btn btn-flat btn-floating"
                                onclick={onShowCorpMenu} >
                            <i class="material-icons">more_horiz</i>
                        </a>
                        <a href="javascript:void(0)" if={config.READ_ONLY} onclick={SkE.showCorpusInfo.bind(this, corpus.corpname)}>
                            <i class="material-icons">info</i>
                        </a>
                    </td>
                </tr>
            </tbody>
            <tfoot ref="last">
            </tfoot>
        </table>
    </div>
    <ul id="myCorpMenu" class="dropdown-content horizontalDropdown">
        <li each={o in store.corpMenuItems}
                data-item={o.type}
                title={_(o.labelId)}>
            <i class="material-icons">{o.icon}</i>
        </li>
    </ul>

    <script>
        const {AppStore} = require('core/AppStore.js')
        const {CorpusStore} = require("corpus/CorpusStore.js")
        const {UserDataStore} = require("core/UserDataStore.js")
        const {Auth} = require('core/Auth.js')
        const FuzzySort = require('libs/fuzzysort/fuzzysort.js')
        require("ca/ca-corpus-download-dialog.tag")

        this.store = CorpusStore
        this.data = this.store.data
        this.username = Auth.getUsername()
        this.isFullAccount = Auth.isFullAccount()
        this.sort = {
            sort: UserDataStore.getOtherData("corpus_select_sort") || 'asc',
            orderBy: UserDataStore.getOtherData("corpus_select_order_by") || 'name'
        }
        this.showLimit = 60
        this.searchQuery = ""
        this.space = Auth.getSpace()

        this.mixin("tooltip-mixin")

        onSuffixIconClick(evt) {
            evt.preventUpdate = true
            this.searchQuery = ""
            this.filterCorpora()
            $(".fuzzy-input input", this.root).focus()
        }

        sortCorpora(){
            this.visibleCorpora = this.store.sort(this.visibleCorpora, this.sort)
        }

        onQueryChangeDebounced(query){
            clearTimeout(this.queryTimer)
            this.queryTimer = setTimeout(function(){
                this.searchQuery = query
                this.showLimit = 60
                this.filterCorpora()
            }.bind(this), 50);
        }

        filterCorpora(query){
            if(this.searchQuery !== ""){
                this.visibleCorpora = []
                let fuzzySorted = FuzzySort.go(this.searchQuery, copy(this.allCorpora), {
                    threshold: -100000,
                    keys: ["language_name", "name"]
                })
                this.visibleCorpora = fuzzySorted.map(fs => {
                    if(fs.score > -Infinity){
                        let c = fs.obj
                        c.score = fs.score
                        c.h_lang = FuzzySort.highlight(fs[0], '<b class="red-text">', "</b>")
                        c.h_corp = FuzzySort.highlight(fs[1], '<b class="red-text">', "</b>")
                        return c
                    }
                }).sort(function(a, b){
                    return Math.sign(b.score - a.score)
                })
            } else{
                this.visibleCorpora = this.allCorpora
                this.sortCorpora()
            }
            this.update()
            this.highlightOccurrences()
        }

        initData(){
            this.corpusListLoaded = AppStore.data.corpusListLoaded
            this.allCorpora = AppStore.get('corpusList') || []
            this.allCorpora = this.allCorpora.filter(corpus => {
                return corpus.owner_name == this.username
            })
            this.visibleCorpora = this.allCorpora
            this.actCorp = AppStore.getActualCorpname()
            this.sortCorpora()
        }
        this.initData()

        onShowCorpMenu(event) {
            this.store.showCorpMenu(event, "#myCorpMenu")
        }

        onSort(sort) {
            this.sort = sort
            this.sortCorpora()
            this.update()
            UserDataStore.saveOtherData({
                    'corpus_select_sort': sort.sort,
                    'corpus_select_order_by': sort.orderBy
                })
        }

        onSelectCorpus(event) {
            this.store.selectCorpus(event.item.corpus)
        }

        onCorpusListLoaded() {
            this.initData()
            this.filterCorpora()
        }

        highlightOccurrences(){
            this.store.highlightOccurrences(this.visibleCorpora, this.refs)
        }

        isNearEnd(){
            var rect = this.refs.last.getBoundingClientRect();
            return rect.bottom <= ((window.innerHeight || document.documentElement.clientHeight) + 1000) //near end
        }

        onScrollDebounced(){
            if(this.data.tab != "my") return
            clearTimeout(this.scrollTimer)
            this.scrollTimer = setTimeout(function(){
                if(this.isNearEnd()){
                    clearTimeout(this.scrollTimer)
                    this.showLimit += 100
                    this.update()
                    this.searchQuery !== "" && this.highlightOccurrences()
                }
            }.bind(this), 50);
        }

        this.on('mount', () => {
            $(window).on("scroll", this.onScrollDebounced)
            AppStore.on('corpusListChanged', this.onCorpusListLoaded)
            $(".fuzzy-input input", this.root).focus()
        })

        this.on('unmount', () => {
            $(window).off("scroll", this.onScrollDebounced)
            AppStore.off('corpusListChanged', this.onCorpusListLoaded)
        })
    </script>
</corpus-tab-my>
