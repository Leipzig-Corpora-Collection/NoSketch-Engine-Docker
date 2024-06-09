<side-nav onmouseenter={onmouseenter} onmouseleave={onmouseleave}>
    <ul id="side-nav" class="sidenav fixed no-autoinit {right-aligned: isRTL}">
        <li id="navMain">
            <a href={logoLink} class="{noSkeLogo: window.config.NO_SKE}">
                <span class="logo"></span>
            </a>
        </li>
        <li if={isAcademic}
            class="academicUseOnly mb-4">
            <div class="academicUseOnly text-center nowrap">
                {_("academicUseOnly")}
                <a href={externalLink("academicSubscription")}
                        target="_blank"
                        class="inlineBlock white-text">
                    <i class="material-icons material-clickable">open_in_new</i>
                </a>
            </div>
        </li>
        <li each="{link in menuLinks}"
                class="feature {'disabled tooltipped': link.disabled}"
                data-page="{link.page}"
                data-position="right"
                data-tooltip={getLinkTooltip(link)}>
            <a href="#{link.href}" id="side_nav_btn{link.page}" class="sidenav-close" onclick={parent.onLinkClick}>
                <i class="small {link.class}">{link.icon}</i>
                <span class="linkText">{getLabel(link)}</span>
            </a>
        </li>
    </ul>

    <script>
        require('./side-nav.scss')
        const {RoutingMeta} = require('core/Meta/Routing.meta.js')
        const {Router} = require('core/Router.js')
        const {AppStore} = require("core/AppStore.js")
        const {Auth} = require("core/Auth.js")
        const {Localization} = require("core/Localization.js")
        this.mixin("tooltip-mixin")


        this.allowShow = true
        this.isRTL = Localization.getDirection() == "rtl"
        this.tooltipEnterDelay = 1300

        updateMenuLinks() {
            let p = window.permissions
            this.menuLinks = [
                {
                    page: "dashboard",
                    labelId: "dashboard",
                    icon: "dashboard",
                    class: "material-icons",
                    disabled: this.isAnonymous && !this.corpus
                },
                {
                    page: this.isAnonymous ? "open" : "corpus",
                    labelId: "selectCorpus",
                    icon: "storage",
                    class: "material-icons"
                },
                {
                    page: "wordsketch",
                    label: "Word Sketch",
                    class: "ske-icons skeico_word_sketch",
                    disabled: !this.features.wordsketch
                },
                {
                    page: "sketchdiff",
                    labelId: "sketchdiff",
                    class: "ske-icons skeico_word_sketch_difference",
                    disabled: !this.features.sketchdiff
                },
                {
                    page: "thesaurus",
                    labelId: "thesaurus",
                    class: "ske-icons skeico_thesaurus",
                    disabled: !this.features.thesaurus
                },
                {
                    page: "concordance",
                    labelId: "concordance",
                    class: "ske-icons skeico_concordance",
                    disabled: !this.features.concordance
                },
                {
                    page: "parconcordance",
                    labelId: "parconcordance",
                    class: "ske-icons skeico_parallel_concordance",
                    tooltip: "t_id:d_parconc_inactive",
                    disabled: !this.features.parconcordance
                },
                {
                    page: "wordlist",
                    labelId: "wordlist",
                    class: "ske-icons skeico_word_list",
                    disabled: !this.features.wordlist
                },
                {
                    page: "ngrams",
                    labelId: "ngrams",
                    class: "ske-icons skeico_n_grams",
                    disabled: !this.features.ngrams
                },
                {
                    page: "keywords",
                    labelId: "keywords",
                    class: "ske-icons skeico_keywords",
                    disabled: !this.features.keywords
                },
                {
                    page: "trends",
                    labelId: "trends",
                    class: "ske-icons skeico_trends",
                    disabled: !this.features.trends
                }
            ].map(obj => {
                obj.href = obj.page
                if(this.corpus && (obj.page == "dashboard" || this.features[obj.page])){
                    obj.href +=  "?corpname=" + this.corpus.corpname
                }
                obj.available = !isDef(p[obj.page]) || p[obj.page]
                obj.disabled = obj.disabled || !obj.available
                return obj
            }, this).sort((a, b) => {
                if(a.available && !b.available){
                    return -1
                } else if(!a.available && b.available){
                    return 1
                } else {
                    return 0
                }
            })
        }

        updateAttributes(){
            this.isAnonymous = Auth.isAnonymous()
            this.isAcademic = Auth.isAcademic()
            this.actualPage = Router.getActualPage()
            this.actualFeature = Router.getActualFeature()
            this.corpus = AppStore.get('corpus')
            this.features = AppStore.get('features')
            this.logoLink = window.config.LOGO_LINK_URL || (this.isAnonymous && !this.corpus ? "#open" : "#dashboard")
            this.updateMenuLinks()
        }
        this.updateAttributes()

        onmouseenter(evt){
            evt.preventUpdate = true
            if(!this.allowShow){
                return
            }
            $(this.root).addClass("show")

            $(document).mousemove(function(){
                // onMouseLeave is not enough, when user click on link and then
                // fast move mouse outside root, mouseleave is not fired - because
                // of tag update.
                if(!$(this.root).is(":hover")){
                    $(document).off("mousemove")
                    $(this.root).removeClass("show")
                }
            }.bind(this))
        }

        onmouseleave(evt){
            evt.preventUpdate = true
            this.allowShow = true
            $(this.root).removeClass("show")
            if(!$("#side-nav").hasClass("open")){ //not mobile side nav version
                $("#side-nav").scrollTop(0)
            }
        }

        onLinkClick(evt){
            evt.preventUpdate = true
            this.allowShow = false
            if(evt.item.link.disabled){
                // click on link of actual page -> nothing to do
                evt.preventDefault()
            } else{
                $(this.root).removeClass("show")
            }
            Dispatcher.trigger("RESET_STORE", evt.item.link.page)
            window.scrollTo(0, 0)
        }

        refreshSidenavPosition(){
            //$("#side-nav").css("top", (window.pageYOffset < 70) ? 70 - window.pageYOffset : 0)
            $("#side-nav").css("top", 0)
        }

        markActiveLink(){
            // not using riot expressions because update() fires mousenter event
            let actualPage = Router.getActualPage()
            let actualFeature = Router.getActualFeature()
            $("li", this.root).each((idx, node) => {
                let li = $(node)
                let page = li.data("page")
                page && li.toggleClass("active", !!(actualPage == page
                        || (actualFeature && RoutingMeta.table[page] && (RoutingMeta.table[page].feature == actualFeature))))
            })
        }

        refreshSideNav(){
            $('.sidenav').sidenav({
                edge: this.isRTL ? "right" : "left",
                menuWidth: 250,
                onOpenStart: () => {$("#side-nav").addClass("open")},
                onCloseEnd: () => {$("#side-nav").removeClass("open")}
            })
        }

        getLinkTooltip(link){
            if(!link.available){
                return _("NAInNoSke", ['<a target="_blank" href="https://sketchengine.eu">Sketch Engine</a>'])
            }
            if(link.disabled){
                if(link.tooltip){
                    return link.tooltip
                }
                return _("db.featureNotAvailable")
            }
            return null
        }

        this.on('update', this.updateAttributes)

        this.on("mount", () => {
            this.markActiveLink()
            $(document).on("scroll", this.refreshSidenavPosition)
            this.refreshSideNav()
            this.refreshSidenavPosition()
            AppStore.on('corpusChanged', this.update)
            AppStore.on("corpusStatusChanged", this.update)
            Dispatcher.on("ROUTER_CHANGE", this.markActiveLink)
        })

        this.on('unmount', () => {
            AppStore.off('corpusChanged', this.update)
            AppStore.off("corpusStatusChanged", this.update)
            Dispatcher.off("ROUTER_CHANGE", this.markActiveLink)
        })

        Dispatcher.on("LOCALIZATION_CHANGE", () => {
            let isRTL = Localization.getDirection() == "rtl"
            if(isRTL != this.isRTL){
                this.isRTL = isRTL
                this.refreshSideNav()
            }
        })
    </script>
</side-nav>
