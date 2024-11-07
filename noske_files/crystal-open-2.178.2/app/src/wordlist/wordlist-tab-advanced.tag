<wordlist-tab-advanced class="wordlist-tab-advanced">
    <a onclick={onResetClick} data-tooltip={_("resetOptionsTip")} class="tooltipped tabFormResetBtn btn btn-floating btn-flat">
        <i class="material-icons color-blue-800">settings_backup_restore</i>
    </a>
    <div class="card-content">
        <div class="mainForm">
            <div class="row">
                <div class="col">
                    <div class="row mb-0">
                        <div class="col">
                            <span class="tooltipped columnShow" data-tooltip="t_id:wl_b_find">
                                {_("find")}
                                <sup>?</sup>
                            </span>
                        </div>
                        <div class="col">
                            <ui-list options={findList}
                                ref="find"
                                value={options.find}
                                name="find"
                                classes="findList"
                                on-change={onFindChange}
                                style="max-width: 250px;"></ui-list>
                        </div>
                        <div class="col">
                            <wordlist-criteria ref="criteria" disabled={options.histid}></wordlist-criteria>
                        </div>
                    </div>
                </div>
                <div class="rightColumn col xl4 l12 m12">
                    <div class="row form-horizontal">
                        <div class="col">
                            <ui-checkbox label-id="wl.excludeWords"
                                name="exclude"
                                checked={options.exclude}
                                disabled={options.histid || (options.filter == "fromList")}
                                on-change={onExlcudeWordsChange}
                            ></ui-checkbox>
                        </div>
                        <div class="col s12 {collapsedBlacklist: !options.exclude}" style="margin-left: 35px;">
                            <expandable-textarea
                                disabled={options.histid || !options.exclude}
                                required="required"
                                validate="1"
                                name="wlblacklist"
                                value={options.wlblacklist}
                                rows="1"
                                label-id={options.exclude ? "wl.pasteListHere" : ""}
                                on-change={onWlblacklistChange}
                                dialog-title={_("wl.excludeWords")}
                                style="max-width: 250px;"></expandable-textarea>
                        </div>
                    </div>

                    <div class="row form-horizontal">
                        <div class="col s12">
                            <ui-checkbox label-id="includeNonwords"
                                disabled={options.histid}
                                name="include_nonwords"
                                checked={options.include_nonwords}
                                on-change={onIncludeNonwordsChange}
                                tooltip="t_id:include_nonwords"
                            ></ui-checkbox>
                        </div>
                    </div>

                    <div class="row" if={!corpus.unicameral}>
                        <div class="col s12">
                            <ui-checkbox
                                label={_("ignoreCase")}
                                name="wlicase"
                                disabled={options.histid}
                                checked={options.wlicase}
                                on-change={onWlicaseChange}
                                tooltip="t_id:wlicase"></ui-checkbox>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col s12">
                            <ui-input
                                type="number"
                                size=8
                                inline=true
                                validate=true
                                min="0"
                                value={options.wlminfreq}
                                label={_("frequency") + " " + _("min")}
                                name="wlminfreq"
                                on-change={onFreqChange}
                                style="margin-right: 15px;"
                                tooltip="t_id:wl_a_wlminfreq"
                            ></ui-input>
                            <ui-input
                                type="number"
                                size=8
                                inline=true
                                validate=true
                                min="0"
                                label={_("frequency") + " " +  _("max")}
                                value={options.wlmaxfreq}
                                name="wlmaxfreq"
                                on-change={onFreqChange}
                                disabled={options.histid}
                                tooltip="t_id:wl_a_wlmaxfreq"
                            ></ui-input>
                        </div>
                    </div>

                    <div class="row">
                        <label class="col s12 control-label">
                            {_("wl.viewResultAs")}
                        </label>
                        <div class="col xl12 l2 m12">
                            <ui-radio options={viewAsOptions}
                                ref="viewAs"
                                riot-value={options.viewAs}
                                name="viewAs"
                                disabled={options.histid}
                                on-change={onViewAsChange}></ui-radio>
                        </div>
                        <div class="col xl12 l10 m12">
                            <wordlist-option-display if={options.viewAs == 2}></wordlist-option-display>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col s12">
                            <subcorpus-select
                                ref="usesubcorp"
                                riot-value={options.usesubcorp}
                                name="usesubcorp"
                                label={_("subcorpus")}
                                on-change={onSubcorpusChange}
                                tooltip="t_id:wl_a_subcorpus"
                                disabled={options.histid || !$.isEmptyObject(options.tts)}
                                style="max-width: 500px;"></subcorpus-select>
                        </div>
                    </div>

                </div>
            </div>
        </div>

        <text-types if={!isAnonymous}
                ref="texttypes"
                disabled={options.usesubcorp != "" || options.histid}
                collapsible=1
                disable-structure-mixing=1
                selection={options.tts}
                on-change={onTtsChange}
                note={options.usesubcorp ?_("subcorpusAndTTWarning") : ""}></text-types>

        <div class="primaryButtons searchBtn">
            <a id="btnGoAdv" class="btn btn-primary" onclick={onSearch}>{_("go")}</a>
        </div>

        <floating-button id="btnGoFloat"
                on-click={onSearch}
                refnodeid="btnGoAdv"></floating-button>
    </div>

    <script>
        require("./wordlist-option-display.tag")
        require("./wordlist-tab-advanced.scss")
        require("./wordlist-option-display-item.tag")
        require("./wordlist-criteria.tag")
        const {AppStore} = require("core/AppStore.js")
        const {Auth} = require("core/Auth.js")
        const {UserDataStore} = require("core/UserDataStore.js")
        const Meta = require("./Wordlist.meta.js")

        this.mixin("feature-child")
        this.mixin("tooltip-mixin")

        this.isAnonymous = Auth.isAnonymous()

        addToList(type, obj){
            this.findList.push({
                type: type,
                label: obj.labelP || obj.label,
                value: obj.value
            })
        }

        updateFindList(){
            this.findList = []
            const lposList = AppStore.get("corpus.lposlist") || []
            const attributes = AppStore.get("corpus.attributes") || []
            const showFirst = ["word", "lemma"]
            attributes.forEach((attr) => {
                if(!attr.isLc && showFirst.indexOf(attr.value) != -1){
                    this.addToList("attr", attr)
                }
            })
            this.store.getDefaultPosAttribute() && lposList.forEach((lpos) => {
                this.addToList("lpos", lpos)
            })
            attributes.forEach((attr) => {
                if(!attr.isLc && showFirst.indexOf(attr.value) == -1){
                    this.addToList("attr", attr)
                }
            })
            this.store.data.findxList.forEach(item => {
                this.findList.push({
                    type: "findx",
                    label: item.name,
                    value: item.id,
                    class: "findx",
                    generator: (item) => {
                        return  `<span class="grey-text">highlight: </span>${item.label} <i class="material-icons right grey-text tooltipped" data-tooltip="t_id:wl_a_highlight" style="font-size:21px;">help_outline</i>`
                    }
                })
            }, this)
        }
        this.updateFindList()


        updateAttributes(){
            this.options = {};
            ["find", "exclude", "filter", "keyword", "wlblacklist", "wlicase",
                    "wlminfreq", "wlmaxfreq", "viewAs",
                    "wlfile", "wlstruct_attr1", "wlstruct_attr2",
                    "wlstruct_attr3", "criteria", "include_nonwords", "histid"].forEach(name => {
                this.options[name] = this.store.data[name]
            })
            this.options.tts = copy(this.store.data.tts)
            this.options.usesubcorp = UserDataStore.getCorpusData(this.corpus.corpname, "defaultSubcorpus") || this.data.usesubcorp
            this.viewAsOptions = Meta.viewAsOptions
        }
        this.updateAttributes()

        onSearch(){
            this.options.page = 1
            if(this.options.viewAs == 2){
                this.options.wlnums = ""
                this.options.wlsort = "frq"
                this.options.relfreq = 0
                this.options.freqcls = 0
            }
            if(this.options.criteria.length && this.options.filter && this.options.keyword){
                this.options.criteria.push({
                    filter: this.options.filter,
                    value: this.options.keyword
                })
                this.options.filter = ""
                this.options.keyword = ""
            }
            this.data.closeFeatureToolbar = true
            this.store.resetSearchAndAddToHistory(this.options)
        }

        onResetClick(){
            this.refs.texttypes && this.refs.texttypes.reset()
            this.store.resetGivenOptions(this.options)
        }

        onFindChange(value, name, label, option){
            this.options.find = value || "word"
            const attr = AppStore.getAttributeByName(this.options.find)
            let lpos = AppStore.getLposByValue(this.options.find)
            if(this.options.filter == "all"){
                this.options.keyword = ""
            }
            if (AppStore.data.wattrs.indexOf(value) == -1) {
                this.options.include_nonwords = false
            }
            if(this.options.histid != (option.type == "findx")){
                if(option.type == "findx"){
                    ["exclude", "filter", "keyword", "wlblacklist", "wlicase",
                    "wlmaxfreq", "viewAs", "usesubcorp", "wlfile", "wlstruct_attr1",
                    "wlstruct_attr2", "wlstruct_attr3", "criteria",
                    "include_nonwords"].forEach(option => {
                        this.options[option] = this.store.defaults[option]
                    }, this)
                    this.options.histid = value
                } else {
                    this.options.histid = ""
                }

                this.refreshTextTypesDisabled()
            }
            this.update()
        }

        onFreqChange(value, name){
            let freq = parseInt(value, 10)
            this.options[name] = isNaN(freq) ? "" : freq
        }

        onIncludeNonwordsChange(checked){
            this.options.include_nonwords = checked
        }

        onExlcudeWordsChange(checked){
            this.options.exclude = checked
            if(!checked){
                this.options.wlblacklist = ""
            }
            this.update()
            delay(() => {
                $("textarea", this.root).focus()
            }, 0)
        }

        onWlicaseChange(checked){
            this.options.wlicase = checked
        }

        onViewAsChange(value){
            this.options.viewAs = value
            if(this.options.viewAs == 1){
                Object.assign(this.options, {
                    "wlstruct_attr1": "",
                    "wlstruct_attr2": "",
                    "wlstruct_attr3": ""
                })
            }
            this.update()
        }

        onWlblacklistChange(value){
            this.options.wlblacklist = value
            this.update()
        }

        onSubcorpusChange(value){
            this.options.usesubcorp = value
            this.refreshTextTypesDisabled()
            this.update()
        }

        turnOnIncludeNonwords(kw) {
            this.options.include_nonwords = !!kw
            this.update()
        }

        refreshTextTypesDisabled(){
            this.refs.texttypes && this.refs.texttypes.setDisabled(!!this.options.usesubcorp || this.options.histid)
        }

        refreshSearchButtonDisable(){
            let disabled = (this.options.filter && ((Meta.filters[this.options.filter].keyword && this.options.keyword === "")
                    || (this.options.filter == "fromList" && this.options.wlfile === "")
                ))
                || (this.options.viewAs == 2 && this.options.wlstruct_attr1 == "")
            $("#btnGoAdv, #btnGoFloat a").toggleClass("disabled", disabled)
        }

        dataChanged(){
            this.updateAttributes()
            this.update()
        }

        findxListLoaded(){
            this.updateFindList()
            this.update()
        }

        onTtsChange(tts){
            this.options.tts = tts
            this.update()
        }

        localizationChange(){
            this.updateFindList()
            this.update()
        }

        this.on("updated", this.refreshSearchButtonDisable)
        this.on("mount", () => {
            this.store.loadFindxList()
            this.refreshSearchButtonDisable()
            // stejne jako basic
            this.store.on("change", this.dataChanged)
            this.store.on("findxListLoaded", this.findxListLoaded)
            Dispatcher.on("LOCALIZATION_CHANGE", this.localizationChange)
        })

        this.on("unmount", () => {
            this.store.off("change", this.dataChanged)
            this.store.off("findxListLoaded", this.findxListLoaded)
            Dispatcher.off("LOCALIZATION_CHANGE", this.localizationChange)
        })
    </script>
</wordlist-tab-advanced>
