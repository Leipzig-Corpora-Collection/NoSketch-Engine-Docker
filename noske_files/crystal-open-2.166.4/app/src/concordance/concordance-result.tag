<concordance-result-items class="rtlNode {opts.class}">
    <span each={item, idxI in opts.data} no-reorder
        if={item.str || item.strc}
        class="itm {item.class} {coll: item.coll} {strc: item.strc}"
        onclick={opts.onClick}
        data-tooltip={item.attr && opts.show_as_tooltips ? item.attr.substr(1) : ""}
        attr={item.attr && !opts.show_as_tooltips && item.attr.substr(1)}
        style="{item.color ? 'color: '  + item.color : ''}">{isDef(item.str) ? (item.str.match(/\S/) ? item.str : "&nbsp;") : null}{item.strc}</span>
</concordance-result-items>

<concordance-result-head class="thead">
    <div class="tr">
        <div class="th" if={parent.v.showLineNumbers}></div>
        <div class="th checkboxTh" if={parent.v.showCheckboxes}>
            <ui-checkbox checked={isAllChecked}
                    tooltip="selectAllToggle"
                    indeterminate={isAnyChecked && !isAllChecked}
                    on-change={onToggleSelectedAll}></ui-checkbox>
        </div>
        <div class="th refTh" if={parent.v.showRefsLeft}>
            <table-label
                class="hide-on-small-only"
                label={_("cc.refs")}
                desc-allowed={false}
                asc-allowed={isRefSortAllowed}
                order-by={"refs"}
                actual-sort={actualSort}
                actual-order-by={ctx}
                on-sort={onRefsSort}>
            </table-label>
        </div>
        <virtual if={parent.data.viewmode == "kwic"}>
            <div class="th right-align">
                <table-label
                    label={_("cc.leftContext")}
                    desc-allowed={false}
                    asc-allowed={true}
                    order-by={corpus.righttoleft ? "1" : "-1"}
                    actual-sort={actualSort}
                    actual-order-by={ctx}
                    on-sort={onSort}>
                </table-label></div>
            <div class="th center-align">
                <table-label
                    label="KWIC"
                    desc-allowed={false}
                    asc-allowed={true}
                    order-by={"0"}
                    actual-sort={actualSort}
                    actual-order-by={ctx}
                    on-sort={onSort}>
                </table-label></div>
            <div class="th" if={data.annotconc}>
                <table-label
                    label={_("an.annotLabel")}
                    desc-allowed={false}
                    asc-allowed={true}
                    order-by="L"
                    actual-sort={actualSort}
                    actual-order-by={ctx}
                    on-sort={onLabelSort}>
                </table-label>
            </div>
            <div class="th left-align">
                <table-label
                    label={_("cc.rightContext")}
                    desc-allowed={false}
                    asc-allowed={true}
                    order-by={corpus.righttoleft ? "-1" : "1"}
                    actual-sort={actualSort}
                    actual-order-by={ctx}
                    on-sort={onSort}>
                </table-label></div>
        </virtual>
        <div if={parent.data.viewmode == "sen"} class="th center-align">{_("sentence")}</div>
        <div if={parent.data.gdex_enabled && parent.data.show_gdex_scores} class="th right-align gdexTh">{_("cc.gdexScore")}</div>
        <div if={parent.v.showCopyButton} class="th copyTh"></div>
    </div>

    <script>
        this.mixin("feature-child")

        let refs = this.data.refs
        let sort = this.data.sort
        this.ctx = null
        this.orderBy = null
        this.refsList = refs != "" ? refs.split(",") : []
        this.isRefSortAllowed = refs != "" && this.refsList[0] != "text" && this.refsList[0] != "#" // cannot sort by token number and document number

        if(sort.length >= 1){
            if(this.refsList.includes("=" + sort[0].attr)){ // sorted by line details
                this.ctx = "refs"
                this.actualSort = sort[0].bward == "r" ? "desc" : "asc"
            } else if(sort.length == 1){
                this.ctx = sort[0].ctx
                this.actualSort = "asc"
            }
        }

        onRefsSort(sort){
            let sorts = this.refsList.map(ref => {
                return {
                    "skey": "kw",
                    "attr": ref[0] == "=" ? ref.substr(1) : ref,
                    "ctx": "0",
                    "bward": sort.sort == "desc" ? "r" : "",
                    "icase": ""
                }
            })
            this.sort(sorts)
        }

        onLabelSort(sort) {
            this.sort([{
                    attr: "label",
                    ctx: "L",
                    labelsort: 1,
                    label: "Label"
                }])
        }

        onSort(sort){
            // {
            //      orderBy: this.orderBy,
            //      sort: this.opts.actualSort
            // }
            this.sort([{
                    "attr": "word",
                    "ctx": sort.orderBy,
                    "bward": sort.sort == "desc" ? "r" : ""
                }])
        }

        sort(sort){
            this.store.searchAndAddToHistory({
                sort: sort,
                page: 1
            })
        }

        onToggleSelectedAll(){
            this.isAllChecked ? this.store.selectedLinesDeselectPage() : this.store.selectedLinesSelectPage()
            this.update()
            $(".tr .td_chb input[type='checkbox']").prop("checked", this.isAllChecked)
            $(".result-table .tbody > .tr").toggleClass("selected", this.isAllChecked)
        }

        _refreshCheckbox(){
            this.isAnyChecked = false
            this.isAllChecked = true
            this.data.items.forEach((item, idx) => {
                let selected = this.store.isLineSelected(item.toknum)
                this.isAnyChecked = this.isAnyChecked || selected
                this.isAllChecked = this.isAllChecked && selected
            }, this)
        }
        this._refreshCheckbox()

        this.on("update", this._refreshCheckbox)

    </script>
</concordance-result-head>


<concordance-result-refs-row class="tr refsUpRow tn-{opts.item.toknum} {selected: parent.store.isLineSelected(opts.item.toknum)}">
    <div if={parent.v.showLineNumbersUp} class="td num">
        {opts.num}
    </div>
    <div if={!parent.v.showLineNumbers && parent.v.showCheckboxes} class="td"></div>
    <div class="td td_refs">
        <span class="refsUp">
            <a class="btn btn-flat btn-floating lineDetail t_lineDetail">
                <i class="material-icons color-blue-200" data-tooltip={_("lineDetailsTip")}>info_outline</i>
            </a>
            <span if={parent.data.refs !== ""}
                    class="refsUpValues"
                    onmouseover={showTooltip}>{opts.item.ref}</span>
        </span>
    </div>
    <div class="td" if={parent.v.showLineNumbersUp && parent.v.showCheckboxes}></div>
    <virtual if={parent.data.viewmode == "kwic"}>
        <div class="td"></div>
        <div class="td"></div>
    </virtual>
    <div if={parent.v.showCopyButton} class="td copyCell"></div>

    <script>
        showTooltip(evt){
            evt.preventUpdate = true
            evt.stopPropagation()
            let node = evt.currentTarget
            if(node.clientWidth < node.scrollWidth){
                let tooltip = window.showTooltip(node, node.innerHTML, 600)
                $(".tooltip-content", tooltip.tooltipEl).css("max-width", "1000px")
            }
        }
    </script>
</concordance-result-refs-row>

<concordance-result class={concordance-result: true,
            fullContext: data.fullcontext && data.viewmode == "kwic",
            directionRTL: corpus.righttoleft,
            directionLTR: !corpus.righttoleft,
            hasAttributes: data.hasAttributes,
            hasContextAttributes: data.hasContextAttributes,
            viewSen: data.viewmode == "sen",
            viewKwic: data.viewmode == "kwic"}>
    <concordance-selected-lines-box></concordance-selected-lines-box>
    <concordance-detail-window structctx={corpus.structctx}></concordance-detail-window>
    <concordance-media-window></concordance-media-window>
    <div if={!data.isLoading && items.length}
            class="table material-table highlight result-table"
            onmouseover={onMouseOver}>
        <concordance-result-head ref="head"></concordance-result-head>
        <div class="tbody {data.annotconc ? "noselect" : ""}">
            <virtual each={item, idx in items} no-reorder key={item.toknum}>
                <concordance-result-refs-row if={v.showRefsUp}
                    item={item}
                    num={(data.itemsPerPage * (data.page - 1)) + idx + 1}
                    onclick={onRefClick}></concordance-result-refs-row>
                <div class="tr tn-{item.toknum} r-{idx + 1} {selected: store.isLineSelected(item.toknum)}">
                    <div if={v.showLineNumbersLeft} class="td num color-blue-200">
                        {(data.itemsPerPage * (data.page - 1)) + idx + 1}
                    </div>
                    <div if={v.showLineNumbersUp && v.showCheckboxes} class="td">
                    </div>
                    <div if={v.showCheckboxes} class="td td_chb">
                        <label for="chb_{idx}">
                            <input type="checkbox"
                                    id="chb_{idx}"
                                    name="chb_{idx}"
                                    class="fill-in"
                                    checked={store.isLineSelected(item.toknum)}
                                    onclick={onLineCheckboxClick}>
                                <span></span>
                            </input>
                        </label>
                    </div>
                    <div if={v.showLineNumbersUp && !v.showCheckboxes} class="td">
                    </div>
                    <div if={v.showRefsLeft}
                            class="td ref {hasRef: item.ref !== ''}"
                            onclick={onRefClick}>
                        <span><i class="material-icons material-clickable t_lineDetail"
                                    data-tooltip={_("lineDetailsTip")}>
                            info_outline</i>&nbsp;
                            <span if={data.refs !== ""}
                                    data-tooltip={(data.shorten_refs && data.refs !== "") ? item.ref : null}
                                    class="ref-label">
                                {(data.refs !== "" && data.ref_size < item.ref.length) ? item.ref.substring(0,data.ref_size)+"..." : item.ref}
                            </span>
                        </span>
                    </div>
                    <virtual if={data.viewmode == "kwic"}>
                        <div class="td leftCol _t" style="text-align: right;"
                                onclick={annotSelectLine.bind(this, item.toknum)}>
                            <concordance-result-items data={isRTL ? item.Right : item.Left}
                                    class="leftCtx"
                                    show_as_tooltips={data.show_as_tooltips}></concordance-result-items>
                        </div>
                        <div class="td center-align middle _t rtlNode">
                            <concordance-result-items data={item.Kwic}
                                    class="kwicWrapper"
                                    on-click={onKwicClick.bind(this, item)}></concordance-result-items>
                        </div>
                        <div class="td left-align middle annotconc" if={data.annotconc}>
                            <a href="javascript:void(0);"
                                    onclick={onLabelMenuClick.bind(this, item)}
                                    class="annot annotbox dropdown-trigger">{lngroup2label[item.linegroup_id] || "_"}</a>
                        </div>
                        <div class="td rightCol _t" style="text-align: left;"
                                onclick={annotSelectLine.bind(this, item.toknum)}>
                            <concordance-result-items data={isRTL ? item.Left : item.Right}
                                    class="rightCtx"
                                    show_as_tooltips={data.show_as_tooltips}></concordance-result-items>
                        </div>
                    </virtual>

                    <virtual if={data.viewmode == "sen"}>
                        <div class="td rtlNode {data.annotconc ? "annotconc" : ""}"
                                style="{corpus.righttoleft ? 'text-align: right;' : ''}">
                            <concordance-result-items data={item.Left}
                                    class="leftCtx _t"
                                    onclick={annotSelectLine.bind(this, item.toknum)}
                                    show_as_tooltips={data.show_as_tooltips}></concordance-result-items>
                            <concordance-result-items data={item.Kwic}
                                    class="kwicWrapper _t"
                                    on-click={onKwicClick.bind(this, item)}></concordance-result-items>
                            <a href="javascript:void(0);"
                                    class="annot annotbox dropdown-trigger"
                                    onclick={onLabelMenuClick.bind(this, item)}
                                    if={data.annotconc}>{lngroup2label[item.linegroup_id] || "_"}</a>
                            <concordance-result-items data={item.Right}
                                    onclick={annotSelectLine.bind(this, item.toknum)}
                                    class="rightCtx _t"
                                    show_as_tooltips={data.show_as_tooltips}></concordance-result-items>
                        </div>
                    </virtual>
                    <div if={data.gdex_enabled && data.show_gdex_scores} class="td gdex">
                        <span class="badge small">
                            {getGDEXScore(item)}
                        </span>
                    </div>
                    <div class="td mediaCell" if={v.showMediaIcon}>
                        <i each={link in item.Links} no-reorder
                                class="material-icons tooltipped red-text"
                                data-tooltip={getIconTooltip(link)}
                                data-position="left"
                                onclick={onOpenMediaClick}>{link.icon}</i>
                    </div>
                    <div  if={v.showCopyButton}
                            class="td copyCell">
                        <i class="material-icons"
                                data-position="left"
                                data-tooltip={_("copyLine")}
                                onclick={onCopyIconClick}>file_copy</i>
                    </div>
                </div>
            </virtual>
        </div>
    </div>

    <concordance-jump-to if={data.sort && data.sort.length && data.total > 10 && !data.isLoading}></concordance-jump-to>

    <ui-pagination
        if={data.total > 10 && !data.isLoading}
        count={data.total}
        items-per-page={data.itemsPerPage}
        actual={data.page}
        on-change={store.changePage.bind(store)}
        on-items-per-page-change={store.changeItemsPerPage.bind(store)}
        show-prev-next={true}></ui-pagination>

    <script>
        const {Localization} = require("core/Localization.js")
        const {AnnotationStore} = require('annotation/annotstore.js')

        require("./concordance-result.scss")
        require("./concordance-detail-window.tag")
        require("./concordance-media-window.tag")
        require("./concordance-line-detail-dialog.tag")
        require("./concordance-jump-to.tag")
        require("./concordance-selected-lines-box.tag")

        this.mixin("feature-child")
        this.mixin("tooltip-mixin")

        this.selectedToknums = []
        this.lastSelectedToknum = -1
        this.lastSelectedLineIdx = null

        this.lngroup2label = {}
        this.annotation_group = AnnotationStore.annotation_group


        onLabelMenuClick(item, evt){
            evt.preventUpdate = true
            evt.stopPropagation()
            let menuNode = $(evt.target)
            if(menuNode.attr("data-target")){
                // recreate each time, list of labels might change
                let instance = M.Dropdown.getInstance(menuNode)
                instance && instance.destroy()
            }
            let id = "ts_" + Date.now() + Math.floor((Math.random() * 10000))
            let ul = $("<ul>", {class: "dropdown-content annotmenu", id: id} ).appendTo($("body"))
            AnnotationStore.labels.forEach(label => {
                let aNode = $("<a>").appendTo($("<li>").appendTo(ul))
                    .on("click", this.labelLine.bind(this, item.toknum, label))
                $("<span>", {html: label.label, class: (label.label.indexOf('.')>=0 ? "leftpad" : "")}).appendTo(aNode)
            }, this)
            if(this.annotation_group == "ivdnt" && item.linegroup_id){
                let aNode = $("<a>", {html: _("an.useExample")}).appendTo($("<li>").appendTo(ul))
                    .on("click", AnnotationStore.addLabelExample.bind(AnnotationStore, item, ""))
            }
            menuNode.attr("data-target", id)
                .dropdown({
                    constrainWidth: false,
                    closeOnClick: true
                })
                .dropdown("open")
        }

        updateAttributes(){
            this.isRTL = Localization.getDirection() == "rtl" && this.corpus.righttoleft
            this.showResultsFrom = (this.data.page - 1) * this.data.itemsPerPage
            this.lngroup2label = AnnotationStore.lngroup2label
            this.items = this.data.items
            let showRefsLeft            = !this.data.refs_up || this.data.refs === ""
            let showRefsUp              = !showRefsLeft
            let showLineNumbers         = this.data.linenumbers
            let showCheckboxes          = this.data.checkboxes
            let showCopyButton          = this.data.showcopy
            let showLineNumbersLeft     = showLineNumbers && !showRefsUp
            let showLineNumbersUp       = showLineNumbers && showRefsUp
            let showMediaIcon           = this.items.some(i => {return i.Links.length})
            this.v = {showRefsLeft, showCheckboxes, showRefsUp, showLineNumbers, showLineNumbersLeft, showLineNumbersUp, showMediaIcon, showCopyButton}
        }
        this.updateAttributes()

        onKwicClick(item, evt){
            let toknum = item.toknum
            $(".tr.kwicDetailDisplayed", this.root).toggleClass("kwicDetailDisplayed", false) //in case detail was opened and user click another row
            this.toggleRowHighlight(toknum, true)
            Dispatcher.trigger("concordanceShowDetail", {
                cols: [{
                    corpname: this.store.corpus.corpname,
                    toknum: toknum,
                    hitlen: item.hitlen
                }],
                corpname: this.store.corpus.corpname,
                structs: this.store.getStructs(),
                onClose: this.toggleRowHighlight.bind(this, toknum, false)
            }, evt)
        }

        onRefClick(evt){
            evt.preventUpdate = true

            let toknum = evt.item.item.toknum
            $(".tr.kwicDetailDisplayed", this.root).toggleClass("kwicDetailDisplayed", false) //in case detail was opened and user click another row

            this.toggleRowHighlight(toknum, true)
            Dispatcher.trigger("openDialog", {
                tag: "concordance-line-detail-dialog",
                class: "modal-line-detail",
                opts: {
                    store: this.store,
                    toknum: toknum
                },
                buttons: [{
                    label: _("save"),
                    class: "btn-primary",
                    onClick: (dialog) => {
                        dialog.contentTag.save()
                    }
                }],
                fixedFooter: 1,
                big: 1,
                tall: 1,
                onClose: this.toggleRowHighlight.bind(this, toknum, false)
            })
        }

        onLineCheckboxClick(evt){
            evt.preventUpdate = true
            this.toggleLineSelection(evt.item.idx, evt.shiftKey)
            this.lastSelectedLineIdx = evt.item.idx
            this.refs.head.update()
        }

        onCopyIconClick(evt){
            evt.preventUpdate = true
            if(evt.ctrlKey || event.metaKey){
                this.toggleLineSelection(evt.item.idx, evt.shiftKey)
            } else {
                window.copyToClipboard(this.store.getLineCopyText(evt.item.item), SkE.showToast.bind(null, _("copied")))
            }
            this.lastSelectedLineIdx = evt.item.idx
        }

        annotSelectLine(tn, evt) {
            evt.preventUpdate = true
            if (this.data.annotconc) {
                let shift = evt.shiftKey
                if (!shift) {
                    let idx = this.selectedToknums.indexOf(tn)
                    if (idx >= 0) {
                        this.selectedToknums.splice(idx, 1)
                        document.getElementsByClassName("tn-" + tn)[0].classList.remove("selected_annot")
                    }
                    else {
                        this.selectedToknums.push(tn)
                        document.getElementsByClassName("tn-" + tn)[0].classList.add("selected_annot")
                    }
                }
                else {
                    if (this.lastSelectedToknum >= 0) {
                        let i = 0
                        while (this.items[i].toknum != this.lastSelectedToknum && this.items[i].toknum != tn) {
                            i += 1
                        }
                        this.selectedToknums.push(this.items[i].toknum)
                        document.getElementsByClassName("tn-" + this.items[i].toknum)[0].classList.add("selected_annot")
                        i += 1
                        while (this.items[i].toknum != this.lastSelectedToknum && this.items[i].toknum != tn && i < this.items.length) {
                            this.selectedToknums.push(this.items[i].toknum)
                            document.getElementsByClassName("tn-" + this.items[i].toknum)[0].classList.add("selected_annot")
                            i += 1
                        }
                        this.selectedToknums.push(this.items[i].toknum)
                        document.getElementsByClassName("tn-" + this.items[i].toknum)[0].classList.add("selected_annot")
                    }
                }
                this.lastSelectedToknum = tn
            }
        }

        onOpenMediaClick(evt){
            evt.preventUpdate = true
            Dispatcher.trigger("concordanceOpenMedia", {...evt.item.link})
        }

        onMouseOver(evt){
            evt.preventUpdate = true
            let tooltip = jQuery(evt.target).data().tooltip
            tooltip && window.showTooltip(evt.target, tooltip, 600)
        }

        toggleLineSelection(idx, shiftKey){
            let selected = !this.store.isLineSelected(this.items[idx].toknum)
            let fromIdx = shiftKey ? Math.min(idx, this.lastSelectedLineIdx) : idx
            let toIdx = shiftKey ? Math.max(idx, this.lastSelectedLineIdx) : idx
            let lines = []
            for(let idx = fromIdx; idx <= toIdx; idx++){
                let line = this.items[idx]
                lines.push({
                    toknum: line.toknum,
                    text: this.store.getLineCopyText(line)
                })
                $(".tn-" + line.toknum).toggleClass("selected", selected)
                $("#chb_" + idx).prop("checked", selected)
            }
            this.store.selectedLinesToggle(lines, selected)
        }

        toggleRowHighlight(toknum, highlight){
            $(".tn-" + toknum).toggleClass("kwicDetailDisplayed", highlight)
        }

        getGDEXScore(item){
            let score = this.data.gdex_scores[item.toknum]
            return isDef(score) ? (score + "").substr(0, 5) : ""
        }

        updateLabels(toknums, lid) {
            for (let i=0; i<toknums.length; i++) {
                for (let j=0; j<this.data.items.length; j++) {
                    if (this.data.items[j].toknum == toknums[i]) {
                        this.data.items[j].linegroup_id = lid
                    }
                }
                Object.keys(this.store.preloadedData).forEach((key) => {
                    if (!isNaN(key)) {
                        let lines = this.store.preloadedData[key].data
                        for (let j=0; j<lines.length; j++) {
                            if (lines[j].toknum == toknums[i]) {
                                lines[j].linegroup_id = lid
                            }
                        }
                    }
                })
            }
        }

        labelLine(toknum, label, event) {
            event.preventUpdate = true
            event.stopPropagation()
            this.annotSelectLine(toknum, event)
            let lid = label ? label.id : 0
            this.selectedToknums.push(toknum)
            AnnotationStore.labelToknums(this.selectedToknums, lid)
            this.updateLabels(this.selectedToknums, lid)
            this.selectedToknums = []
            let selectedLines = document.querySelectorAll(".tr.selected_annot")
            for (let i=0; i<selectedLines.length; i++) {
                selectedLines[i].classList.remove("selected_annot")
            }
            $(`.tn-${toknum} .annotconc .annot`).addClass("disabled")
        }

        getIconTooltip(line){
            let source = line.mediatype || "unknown"
            let fileName = line.url.substring(line.url.lastIndexOf('/') + 1).split("?")[0]
            return _("clickToOpen" + capitalize(source)) + "<br><br><small style=\"white-space: nowrap\">" + fileName + "</small>"
        }

        this.on('updated', () => {
            if (this.data.annotconc) {
                if (this.selectedToknums.length) {
                    for (let i=0; i<this.selectedToknums.length; i++) {
                        let el = document.getElementsByClassName("tn-" + this.selectedToknums[i])
                        if (el.length) {
                            el[0].classList.add("selected_annot")
                        }
                    }
                }
                // TODO: shortcuts for fast annotation
            }
        })

        onLabelSaved(payload){
            payload.request.toknum.split(" ").forEach(toknum => {
                $(`.tn-${toknum} .annotconc .annot`).html(payload.label).removeClass("disabled")
            })
        }

        this.on("update", this.updateAttributes)

        this.on("mount", () => {
            this.store.on("countChange", this.update) // pagination
            AnnotationStore.on("ANNOTATION_SUCCESSFUL", this.onLabelSaved)
        })

        this.on("unmount", () => {
            this.store.off("countChange", this.update)
            AnnotationStore.off("ANNOTATION_SUCCESSFUL", this.onLabelSaved)
        })
    </script>
</concordance-result>
