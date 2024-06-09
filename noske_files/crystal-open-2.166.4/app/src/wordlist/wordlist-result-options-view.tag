<wordlist-result-options-view class="wordlist-result-options-view">
    <div class="row">
      <div class="col l4 m6 s12 dividerRight">
        <ui-switch label-id="singleColumn"
                name="onecolumn"
                disabled={!store.hasBeenLoaded || data.isLoading || data.showtimelines}
                riot-value={data.onecolumn || data.showtimelines}
                tooltip="t_id:wl_r_view_onecolumn"
                on-change={onOptionChange}
                class="lever-right"></ui-switch>
        <ui-switch name="showLineNumbers"
                label-id="showLineNumbers"
                disabled={!store.hasBeenLoaded || data.isLoading}
                riot-value={data.showLineNumbers}
                tooltip="t_id:wl_r_show_view_line_numbers"
                on-change={onOptionChange}
                class="lever-right"></ui-switch>
        <ui-switch if={!data.histid}
                name="bars"
                label-id="wl.bars"
                disabled={!store.hasBeenLoaded || data.isLoading || data.wlstruct_attr1 === ""}
                riot-value={data.bars}
                tooltip="t_id:wl_r_view_bars"
                on-change={onBarsChange}
                class="lever-right"></ui-switch>
        <ui-switch if={data.histid}
                name="showratio"
                label-id="showRatio"
                riot-value={data.showratio}
                on-change={onOptionChange}
                class="lever-right"></ui-switch>
        <ui-switch if={data.histid}
                name="showrank"
                label-id="showRank"
                riot-value={data.showrank}
                on-change={onOptionChange}
                class="lever-right"></ui-switch>
    </div>
    <div if={!data.histid} class="col l4 m6 s12">
        <ui-switch each={attr in attrsList}
                name={attr.value}
                label={attr.label}
                label-id={attr.labelId}
                tooltip={attr.tooltip}
                disabled={isAttrDisabled(attr)}
                riot-value={data.cols.includes(attr.value)}
                on-change={onAttrChange}
                class="lever-right"></ui-switch>
    </div>
  </div>

    <script>
        require("./wordlist-result-options.scss")
        const Meta = require("./Wordlist.meta.js")

        this.mixin("feature-child")

        this.attrsList = copy(Meta.wlnumsList)
        this.corpus.hasStarAttr && this.attrsList.push({
            labelId: "star",
            value: "star:f",
            tooltip: "t_id:asr"
        })
        this.attrsList = this.attrsList.map(attr => {
            if(attr.value == "docf" && this.corpus.hasStarAttr){
                attr.labelId = "mr"
                attr.tooltip = "t_id:mr"
            }
            if(attr.value == "reldocf" && this.corpus.hasStarAttr){
                attr.labelId = "relmr"
                attr.tooltip = "t_id:relmr"
            }
            return attr
        })
        if(!this.corpus.hasDocfAttr){
            this.attrsList = this.attrsList.filter(attr => attr.value != "docf" && attr.value != "reldocf")
        }

        onOptionChange(value, name){
            this.store.changeValue(value, name)
            this.store.saveUserOptions([name])
            this.store.updateUrl(true)
        }

        onAttrChange(checked, name, evt, tag){
            let isInCols = this.data.cols.includes(name)
            if(checked && !isInCols){
                this.data.cols.push(name)
            } else if(!checked && isInCols){
                this.data.cols = this.data.cols.filter(a => a != name)
            }
            this.store.sortCols()
            let needReload = (name != "reldocf" || !this.data.cols.includes("docf"))
                    && checked
                    && !this.store.isStructuredWordlist()
                    && (!this.data.items.length || this.data.cols.some(a => !isDef(this.data.items[0][a])))
            if(needReload){
                this.store.searchAndAddToHistory({
                    page: 1
                })
            } else {
                this.store.updatePageTag()
            }
            this.store.saveUserOptions()
            this.store.updateUrl(true)
        }

        onBarsChange(bars){
            this.store.changeValue(bars, "bars")
            this.store.saveUserOptions(["bars"])
        }

        isAttrDisabled(attr){
            let isStruct = this.store.isStructuredWordlist()
            return !this.store.hasBeenLoaded
                    || this.data.isLoading
                    || (isStruct && !["frq", "relfreq"].includes(attr.value))
                    || (isStruct && attr == "relfreq" && this.data.raw.concsize == this.data.raw.fullsize)
        }
    </script>
</wordlist-result-options-view>
