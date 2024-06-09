<page-corpus class="page-corpus">
    <introduction if={!skipWizard && isFullAccount && !noSkeNoCa}></introduction>
    <div class="pt2">
        <div class="form card mt-0">
            <ui-tabs if={isFullAccount}
                    name="corpus-tabs"
                    tabs={tabs}
                    active={tab}
                    on-tab-change={onTabChange}>
            </ui-tabs>
            <corpus-tab-advanced if={!isFullAccount}></corpus-tab-advanced>
        </div>
    </div>

    <script>
        require("./page-corpus.scss")
        require("./corpus-tab-basic.tag")
        require("./corpus-tab-advanced.tag")
        require("./corpus-tab-my.tag")
        require("./corpus-tab-shared.tag")
        require("./introduction.tag")
        const {UserDataStore} = require("core/UserDataStore.js")
        const {CorpusStore} = require("corpus/CorpusStore.js")
        const {AppStore} = require("core/AppStore.js")
        const {Auth} = require("core/Auth.js")

        this.noSkeNoCa = window.config.NO_SKE || window.config.NO_CA
        this.skipWizard = true
        this.isFullAccount = Auth.isFullAccount()
        this.languageCount = AppStore.get("languageList").length
        this.tabs = [{
            tabId: "advanced",
            labelId: "advanced",
            tag: "corpus-tab-advanced"
        }, {
            tabId: "my",
            labelId: "cp.my",
            tag: "corpus-tab-my"
        }]
        this.tab = CorpusStore.get("tab")
        if(this.tabs.findIndex(t => t.tabId == this.tab) == -1){
            this.tab = this.tabs[0].tabId
        }

        onTabChange(tabId){
            CorpusStore.changeTab(tabId)
            $(".fuzzy-input:visible input").focus()
        }

        updateIntro() {
            this.skipWizard = UserDataStore.data.globalDataLoaded
                    ? UserDataStore.data.global.skipWizard
                    : true
            this.update()
        }

        this.on("mount", () => {
            UserDataStore.on("globalChange", this.updateIntro)
        })

        this.on("unmount", () => {
            UserDataStore.off("globalChange", this.updateIntro)
        })
    </script>
</page-corpus>
