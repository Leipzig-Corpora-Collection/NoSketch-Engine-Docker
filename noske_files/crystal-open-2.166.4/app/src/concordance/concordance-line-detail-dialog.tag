<concordance-line-detail-dialog class="concordance-line-detail-dialog {directionRTL: corpus.righttoleft}">
    <h4>{_("lineDetailTitle")}</h4>
    <div class="grey-text">
        <raw-html content={_("lineDetailDesc", ['<i class="material-icons rotate90CW color-blue-800" style="opacity:0.6; vertical-align: text-bottom;">insert_chart</i>'])}></raw-html>
    </div>
    <span class="inline-block options">
        <ui-checkbox
            inline=1
            checked={data.refs_up}
            label-id="cc.displayAboveLines"
            tooltip="aboveLinesTip"
            name="refs_up"
            on-change={onRefsUpChange}></ui-checkbox>
        <virtual if={!data.refs_up}>
            <ui-checkbox
                inline={true}
                disabled={data.refs_up}
                checked={data.shorten_refs}
                label-id="cc.shortenBeg"
                name="shorten_refs"
                on-change={onOptionChange}></ui-checkbox>
            <ui-input
                inline={true}
                disabled={!data.shorten_refs}
                type="number"
                min="1"
                name="ref_size"
                size=3
                on-change={onOptionChange}
                riot-value={data.shorten_refs ? data.ref_size: ""}></ui-input>
            <span class="color-blue-800">
                {_("cc.shortenEnd")}
            </span>
        </virtual>
    </span>

    <div class="clearfix"></div>

    <div class="hide-on-small-only">
        <div class="card concordance-result">
            <div class="card-content">
                <span class="right arrows">
                    <a class="iconButton btn btn-flat btn-floating ldtt {disabled: !prevLine}"
                            data-tooltip={_("showPrevLine")}
                            onclick={prevLine ? showLine.bind(this, prevLine.toknum) : null}>
                        <i class="material-icons grey-text">arrow_upward</i>
                    </a>
                    <a class="iconButton btn btn-flat btn-floating ldtt {disabled: !nextLine}"
                            data-tooltip={_("showNextLine")}
                            onclick={nextLine ? showLine.bind(this, nextLine.toknum) : null}>
                        <i class="material-icons grey-text">arrow_downward</i>
                    </a>
                </span>
                <div class="result-table">
                    <div class="leftCol _t rtlNode">
                        <concordance-result-items data={line.Left}></concordance-result-items>
                    </div>
                    <div class="center-align middle _t rtlNode">
                        <span each={kwic in line.Kwic} class="kwicWrapper">
                            <span class="itm">{kwic.str}</span>
                        </span>
                    </div>
                    <div class="rightCol _t rtlNode">
                        <concordance-result-items data={line.Right}></concordance-result-items>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div if={!isLoading}>
        <ui-filtering-list ref="list"
            name="lineDetails"
            multiple=1
            label=" "
            show-all={true}
            options={list}
            riot-value={references}
            on-show-selected-change={onShowSelectedChange}></ui-filtering-list>
            <div class="center-align">
                <a if={!showAll} id="btnShowAll" class="btn" onclick={onShowAllClick}>{_("showAll")}</a>
            </div>
    </div>

    <div if={isLoading} class="center-align loading">
        <preloader-spinner></preloader-spinner>
    </div>

    <script>
        const {Connection} = require("core/Connection.js")
        require("./concordance-line-detail-dialog.scss")
        this.mixin("tooltip-mixin")

        this.store = this.opts.store
        this.data = this.store.data
        this.corpus = this.store.corpus

        this.tooltipClass = ".ldtt"
        this.isLoading = true
        this.list = [];
        this.showAll = false
        this.toknum = this.opts.toknum

        this.references = this.data.refs ? this.data.refs.split(",").map(r => {
            if(r[0] == "="){
                return r.slice(1)
            }
            return r
        }) : []
        let allowed = this.store.refList
        this.references = this.references.filter(ref => {
            return ref == "#"
                    || ref == this.corpus.docstructure
                    || allowed.findIndex(r => {
                        return r.value == ref
                    }) != -1
        }, this)

        onShowSelectedChange(){
            this.onShowAllClick()
            this.update()
        }

        updateAttributes(){
            this.items = this.data.items

            let lineIdx = this.items.findIndex( i => {
                return i.toknum == this.toknum
            })
            this.line = this.items[lineIdx]
            this.prevLine = this.items[lineIdx -1]
            this.nextLine = this.items[lineIdx +1]
        }
        this.updateAttributes()

        optionGenerator(item){
            let html = ""
            if(item.value != "#" && item.value != this.corpus.docstructure){ //exclude token number, and doc structure
                html += "<a href=\"" + this._getFrequencyLink(item) +  "\">"
                        + "<i class=\"material-icons rotate90CW right goToFrequency ldtt\" data-tooltip=\""
                        + _("cc.showFrequency") + "\">insert_chart"
                        +"</i>"
                        +"</a>"
            }
            html += "<span class=\"ld_label\">" + getLabel(item) + "</span>"
            if(window.isURL(item.rowVal)){
                html += "<span class=\"ld_value\">"
                html += "<a href=\"" + item.rowVal + "\" target=\"_blank\">"
                html += (isDef(item.rowVal) ? item.rowVal : "") + "</span>"
                html += "</a>"
            } else{
                html += "<span class=\"ld_value\">" + (isDef(item.rowVal) ? item.rowVal : "") + "</span>"
            }
            return html
        }

        _getFrequencyLink(item){
            return this.store.f_getLink({f_texttypes: [item.value + " 0"]} ,"texttypes", "advanced")
        }

        save(){
            this.store.searchAndAddToHistory({
                refs: this.refs.list.refs.list.value.map(r => {
                    return (r != "#" && r != this.corpus.docstructure) ? ("=" + r) : r //with "=" in the beginning makes bonito to return values without "<key>="
                }).join(",")
            })
            Dispatcher.trigger("closeDialog")
        }

        onRefsUpChange(refs_up){
            if(!refs_up){
                this.data.shorten_refs = false
            }
            this.onOptionChange(refs_up, 'refs_up')
        }

        onOptionChange(value, name){
            this.data[name] = value
            this.store.saveUserOptions([name])
            this.update()
        }

        showLine(toknum){
            this.toknum = toknum
            this.updateAttributes()
            this.load()
            this.update()
        }

        refreshList(){
            this.list = [{
                value: "#",
                labelId: "cc.tokenNumber",
                rowVal: this.toknum,
                generator: this.optionGenerator
            }, {
                value: this.corpus.docstructure,
                labelId: "cc.documentNumber",
                rowVal: this.dataObj[this.corpus.docstructure + "#"],
                generator: this.optionGenerator
            }]
            // do not change generators in shared refList
            let refListCopy = JSON.parse(JSON.stringify(this.store.refList))
            let list = refListCopy.map(function(r){
                r.generator = this.optionGenerator
                if(this.dataObj[r.value]){
                    r.rowVal = this.dataObj[r.value]
                }
                return r
            }.bind(this))

            if(!this.showAll){
                let everythingIsVisible = true
                list = list.filter(function(r) {
                    if(isDef(r.rowVal)){
                        return true
                    } else{
                        everythingIsVisible = false
                        return false
                    }
                    return isDef(r.rowVal)
                }.bind(this))
                if(everythingIsVisible){
                    this.showAll = true
                }
            }

            list.sort( (a, b) => {
                // items with values first, then alphabetically
                if (isDef(a.rowVal)){
                    if(isDef(b.rowVal)){
                        return getLabel(a).localeCompare(getLabel(b))
                    }
                    return -1
                } else{
                    if(isDef(b.rowVal)){
                        return 1
                    } else{
                        return getLabel(a).localeCompare(getLabel(b))
                    }
                }
            })

            this.list = this.list.concat(list)
        }

        load(){
            this.isLoading = true
            Connection.get({
                url: window.config.URL_BONITO + "fullref",
                data: {
                    pos: this.toknum,
                    corpname: this.corpus.corpname
                },
                done: this.onDataLoaded.bind(this),
                fail: payload => {
                    SkE.showError("Could not load concordance data.", getPayloadError(payload))
                }
            })
        }

        onDataLoaded(payload){
            this.isLoading = false
            this.dataObj = {}
            payload.Refs.forEach(d => {
                this.dataObj[d.id] = d.val
            })
            this.refreshList()
            this.update()
        }

        onShowAllClick(){
            this.showAll = true
            this.refreshList()
        }

        this.on("update", this.updateAttributes)

        this.on("mount", () => {
            this.load()
        })
    </script>
</concordance-line-detail-dialog>
