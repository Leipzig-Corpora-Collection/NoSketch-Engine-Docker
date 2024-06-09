<header-navbar class='header-navbar'>
    <div class="noScreen center-align mb-4">
        <img src="images/logo_bw_small.png">
    </div>
    <nav>
        <div class='nav-wrapper'>
            <a id="mobileMenu" href='#' data-target='side-nav' class='sidenav-trigger hide-on-large-only'>
                <i class='material-icons'>menu</i>
            </a>
            <div id="headerMiddle">
                <h1> {title}</h1>
                <header-corpus></header-corpus>
            </div>
            <div id="headerRight" class="right">
                <div class="accountBar">
                    <a href="{window.config.URL_RASPI}#pay/subscribe"
                            if={showSubscribe}
                            class="subscribeBtn btn btn-primary">
                        {_("subscribe")}
                    </a>
                    <span if={showSubscribe && daysLeft !== null} class="daysLeft">
                        {_("daysLeft", [daysLeft])}
                    </span>
                    <div if={isAnonymous} class="anonymousUser grey-text">
                        {_("notLoggedIn")}
                        <br>
                        <a href={window.config.URL_LOGIN} class="blue-text">{_("logIn")}</a>
                    </div>
                    <div if={!isAnonymous} class="grey-text">
                        {_("loggedIn")}
                        <br>
                        <span class="blue-text">{user.username}</span>
                    </div>
                    <span class="siteLicence">
                        <div if={isSiteLicenceMember} class="licenceName grey-text">
                            {session.site_licence.name}
                        </div>
                        <div if={isSiteLicence} class="requestMoreSpace hide-on-small-only">
                            <a href="javascript:void(0);"
                                    onclick={onRequestMoreSpaceClick}
                                    class="navbar_tt"
                                    data-tooltip={_("getMoreSpaceTip")}>
                                {_("getMoreSpace")}
                                <i class="material-icons">add_circle_outline</i>
                            </a>
                        </div>
                    </span>
                </div>
                <header-menu></header-menu>
            </div>
        </div>
    </nav>
    <div class="clearfix"></div>

    <script>
        require('core/header/header-corpus.tag')
        require('core/header/header-navbar.scss')
        require('core/header/header-menu.tag')
        const {Router} = require('core/Router.js')
        const {Auth} = require("core/Auth.js")
        const {Connection} = require("core/Connection.js")
        const Dialogs = require("dialogs/dialogs.js")


        this.showSubscribe = false
        this.daysLeft = null
        this.tooltipClass = ".navbar_tt"
        this.mixin("tooltip-mixin")

        updateAttributes(){
            this.title = Router.getActualPageLabel()
            this.user = Auth.getUser()
            this.session = Auth.getSession()
            this.isAnonymous = Auth.isAnonymous()
            this.isTrial = this.user.licence_type == "trial"
            this.isSiteLicenceMember = Auth.isSiteLicenceMember()
            this.isSiteLicence = Auth.isSiteLicence()
        }
        this.updateAttributes()

        refreshSubscribeButton(){
            !window.config.NO_CA && delay(() => {
                Connection.get({
                    url: window.config.URL_CA + "users/me/can_subscribe",
                    xhrParams: {
                        method: 'POST',
                        data: JSON.stringify({}),
                        contentType: "application/json"
                    },
                    always: (payload) => {
                        let wasSubscribe = this.showSubscribe
                        this.showSubscribe = payload && payload.result
                        wasSubscribe != this.showSubscribe && this.update()
                    }
                })
            }, 2000)
        }

        onUserChange(){
            this.updateAttributes()
            this.refreshSubscribeButton()
            this.update()
        }

        onRequestMoreSpaceClick(){
            Dialogs.showRequestMoreSpaceDialog()
        }

        onPayDataLoaded(payload){
            if(payload.data.end_date){
                this.daysLeft = Math.ceil((new Date(payload.data.end_date) - new Date()) / (1000 * 60 * 60 * 24))
                this.update()
            }
        }

        this.on("update", this.updateAttributes)

        this.on('mount', () => {
            Dispatcher.on("AUTH_LOGIN", this.onUserChange)
            Dispatcher.on("PAY_USER_DATA_LOADED", this.onPayDataLoaded)
        })

        this.on("unmount", () => {
            Dispatcher.off("AUTH_LOGIN", this.onUserChange)
        })

        Dispatcher.on("ROUTER_CHANGE", () => {
            this.isMounted && this.update({
                title: Router.getActualPageLabel()
            })
        })

        Dispatcher.on("APP_READY_CHANGED", () => {
            this.refreshSubscribeButton()
        })

    </script>
</header-navbar>
