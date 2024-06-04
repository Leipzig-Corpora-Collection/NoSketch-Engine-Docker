<wordlist-result-options class="wordlist-result-options">
    <span class="inline-block">
        <a href="javascript:void(0);"
                if={data.raw.concsize && data.raw.concsize < data.raw.fullsize}
                id="wlRandomToggleBtn"
                class="randomBtn"
                onclick={onRandomClick}>
            <i class="material-icons tooltipped inlineBlock {red-text: !data.random}"
                    data-tooltip={_(data.random ? "usingRandom10M" : "usingFirst10M")}>
                error
            </i>
        </a>
        <subcorpus-chip></subcorpus-chip>
        <text-types-chip></text-types-chip>
        <h4 class="ro-title text-primary pull-left">{resultsFor}</h4>
        <span class="totalItems color-blue-200" if={totalitems || data.totalfrq}>
            (<span if={totalitems}>{totalitems}&nbsp;{_("wl.items")}</span>
            <span if={totalitems && data.totalfrq}>| </span>
            <span if={data.totalfrq}>{window.Formatter.num(data.totalfrq)}&nbsp;{_("totalFrq")}</span>)
        </span>
        <result-filter-chip></result-filter-chip>
    </span>

    <feature-toolbar ref="feature-toolbar"
            store={store}
            pulse-id={pulseId}
            feature-page="wordlist"
            formats={["csv", "xlsx", "xml"]}
            options={isAttribute ? [] : optionsList}
            settings-tag={isAttribute ? null : "wordlist-tabs"}></feature-toolbar>

    <script>
        require("./wordlist-result-options.scss")
        require("wordlist/wordlist-tabs.tag")
        require("wordlist/wordlist-result-options-view.tag")
        require('common/result-info/result-info.tag')

        this.mixin("feature-child")
        this.mixin("tooltip-mixin")

        onRandomClick(){
            this.store.searchAndAddToHistory({
                random: !this.store.data.random * 1 // numeric value 1/0
            })
        }

        updateAttributes(){
            this.optionsList = [{
                    id: "view",
                    icon: "visibility",
                    iconClass: "material-icons",
                    contentTag: "wordlist-result-options-view",
                    labelId: "changeDisplayOptions"
                }, {
                    id: "filter",
                    contentTag: 'result-filter',
                    disabled: this.data.jobid,
                    contentOpts: {
                        hideMatchCase: this.data.wlicase
                    },
                    iconClass: "material-icons",
                    icon: "filter_list",
                    labelId: 'filterResults'
                }, {
                    id: "info",
                    contentTag: 'result-info',
                    contentOpts: {
                        doNotRemove: ["wlattr"]
                    },
                    iconClass: "material-icons",
                    icon: "info_outline",
                    labelId: 'wl.labelInfo'
                }]
            this.resultsFor =  this.store.getValueLabel(this.data.find, "find")
            this.totalitems = isNaN(this.data.totalitems) ? "" : window.Formatter.num(this.data.totalitems)
            this.store.request[0].relfreq = this.data.relfreq
            this.store.request[0].freqcls = this.data.freqcls
            this.pulseId = null
            if((this.data.isEmpty || this.data.isEmptySearch) && !this.data.jobid){
                this.pulseId = this.data.search_query === "" ? "settings" : "filter"
            }
        }
        this.updateAttributes()

        this.on("update", this.updateAttributes)
    </script>
</wordlist-result-options>
