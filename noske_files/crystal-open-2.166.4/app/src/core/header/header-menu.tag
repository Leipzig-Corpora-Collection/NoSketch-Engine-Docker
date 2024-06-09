<header-menu-item>
    <li id={"header-menu-" + opts.data.id}>
        <a id="btn{opts.data.id}"
                onclick={opts.data.onClick ? opts.data.onClick : null}
                href={opts.data.href}
                class="relative {header_tt: opts.showTooltip}"
                data-tooltip={opts.showTooltip ? _(opts.data.labelId) : ""}>
            <i class='material-icons'>{opts.data.icon}</i>
            <span if={opts.data.active} class="activeIcon"></span>
            <label>{getLabel(opts.data)}</label>
        </a>
    </li>
</header-menu-item>


<header-menu class="header-menu">
    <ul id="menuList" class='right'>
        <header-menu-item if={!showMobileMenu && item.inMenu && !item.hide}
                each={item in items}
                data={item}
                show-tooltip=1></header-menu-item>
        <li><a id='menuDropdownButton'
                    data-target='menuDropdownList'
                    class='header_tt'
                    data-tooltip={_("moreOptions")}>
                <i class='material-icons'>person_outline</i>
            </a>
        </li>
    </ul>

    <ul id='menuDropdownList' class='dropdown-content'>
        <header-menu-item if={(showMobileMenu || !item.inMenu) && !item.hide}
                each={item in items}
                data={item}></header-menu-item>
    </ul>

    <script>
        const self = this
        require('./header-menu.scss')
        require('dialogs/profile-dialog/profile-dialog.tag')
        require('dialogs/help-dialog/help-dialog.tag')
        require('dialogs/settings-dialog/settings-dialog.tag')
        require('dialogs/login-as-dialog/login-as-dialog.tag')
        require('dialogs/ske-li-dialog/ske-li-dialog.tag')

        const {AppStore} = require('core/AppStore.js')
        const {Auth} = require('core/Auth.js')

        this.showMobileMenu = false
        this.tooltipClass = ".header_tt"
        this.mixin("tooltip-mixin")

        onProfileClick(){
            Dispatcher.trigger('openDialog', {
                id: "profile",
                tag: 'profile-dialog',
                //title: Auth.getSession().user.full_name,
                width: 700
            })
        }

        onLogoutClick(){
            let loc = (document.location || window.location)
            loc.href = loc.protocol + "//" + "logout:nopassword@" + loc.host
        }

        onHelpClick(){
            Dispatcher.trigger('openDialog', {
                tag: 'help-dialog',
                width: 950
            })
        }

        onLoginAsClick(){
            this.openLoginAsDialog()
        }

        onLoginAsHotkey(){
            // admin or already logged as in -> admin
            (Auth.isSuperUser() || Auth.getSession().emulated_user) && this.openLoginAsDialog()
        }

        onLogoutAsClick(){
            Auth.logoutAs()
        }

        onLocalAdminClick(){
             window.open(window.config.URL_RASPI + "#admin", "_blank")
        }

        onSkeAdminClick(){
             window.open(externalLink("globalAdministration"), "_blank")
        }

        onSettingsClick(evt){
            Dispatcher.trigger('openDialog', {
                tag: 'settings-dialog',
                fixedFooter: true
            })
        }

        onSkeLiClick(){
            Dispatcher.trigger("openDialog", {
                id: "skeLi",
                class: "shortLinkDialog",
                fixedFooter: true,
                title: _("shortlink"),
                tag: "ske-li-dialog"
            })
        }

        refreshMenu(){
            let isFullAccount = Auth.isFullAccount()
            this.items = [{
                hide: !isFullAccount || (!AppStore.data.bgJobs.length && !Auth.isSuperUser()),
                id: "bgjobs",
                labelId: "bgjobs",
                icon: "timelapse",
                inMenu: true,
                active: AppStore.data.bgJobsNotify,
                href: "#bgjobs"
            }, {
                hide: !isFullAccount || !window.config.URL_SKE_LI,
                id: "link",
                labelId: "shortlink",
                icon: "link",
                inMenu: true,
                onClick: this.onSkeLiClick
            }, {
                hide: !isFullAccount || window.config.NO_CA,
                id: "profile",
                labelId: "profile",
                icon: "person",
                inMenu: false,
                onClick: this.onProfileClick
            }, {
                hide: !window.permissions.my,
                id: "myske",
                labelId: "mySke",
                icon: "grade",
                inMenu: false,
                href: "#my"
            }, {
                id: "help",
                labelId: "hp.userGuideTitle",
                icon: "help_outline",
                inMenu: true,
                onClick: this.onHelpClick,
            }, {
                id: "settings",
                labelId: "settings",
                icon: "settings",
                onClick: this.onSettingsClick
            }, {
                hide: isFullAccount,
                id: "login",
                labelId: "logIn",
                icon: "group",
                href: window.config.URL_LOGIN
            }, {
                hide: !Auth.isSiteLicenceAdmin(),
                id: "localAdmin",
                labelId: "localAdmin",
                icon: "domain",
                onClick: this.onLocalAdminClick
            }, {
                hide: !Auth.isSuperUser(),
                id: "skeAdmin",
                labelId: "skeAdmin",
                icon: "public",
                onClick: this.onSkeAdminClick
            }, {
                hide: !Auth.isLoggedAs(),
                id: "logoutAs",
                labelId: "logoutAs",
                icon: "group",
                onClick: this.onLogoutAsClick
            }, {
                hide: !Auth.isSuperUser(),
                id: "loginAs",
                labelId: "loginAs",
                icon: "group",
                onClick: this.onLoginAsClick
            }, {
                hide: !isFullAccount,
                id: "logout",
                labelId: "logout",
                icon: "exit_to_app",
                inMenu: false,
                onClick: this.onLogoutClick
            }]
        }
        this.refreshMenu()


        openLoginAsDialog(){
            Dispatcher.trigger('openDialog', {
                tag: 'login-as-dialog',
                title: _('loginAs'),
                small: true,
                class: "loginAsDialog"
            })
        }

        resize(){
            const vieportWidth = $(window).width()
            if(vieportWidth < 992 && !this.showMobileMenu){
                this.showMobileMenu = true
                this.update()
            } if(vieportWidth >= 993 && this.showMobileMenu){
                this.showMobileMenu = false
                this.update()
            }
        }
        window.addEventListener('resize', () => {
            this.resize()
        })

        this.on("update", this.refreshMenu)

        this.on('mount', () => {
            $(document).ready(function(){
               $('#menuDropdownButton', this.root).dropdown({
                alignment: 'right',
                constrainWidth: false,
                coverTrigger: false
               });
               self.resize()
            })
            Dispatcher.on("AUTH_LOGIN", this.update)
            Dispatcher.on("BGJOBS_UPDATED", this.update)
            Dispatcher.on("LOGIN_AS", this.onLoginAsHotkey)
        })

        this.on("unmount", () => {
            Dispatcher.off("AUTH_LOGIN", this.update)
            Dispatcher.off("BGJOBS_UPDATED", this.update)
            Dispatcher.off("LOGIN_AS", this.onLoginAsHotkey)
        })
    </script>
</header-menu>
