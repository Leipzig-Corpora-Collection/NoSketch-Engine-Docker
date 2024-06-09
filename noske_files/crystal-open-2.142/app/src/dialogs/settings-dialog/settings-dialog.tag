<settings-dialog-general>
    <div class="row">
        <div class="col m5 s12 input-label">
            {_("language")}
        </div>
        <div class="col m7 s12">
            <ui-select
                options={languageOptions}
                value={settings.language}
                name="language"
                on-change={parent.onOptionChange}></ui-select>
        </div>
    </div>

    <div class="row">
        <div class="col m5 s12 input-label">
            {_("opts.density")}
        </div>
        <div class="col m7 s12">
            <ui-select
                options={densityOptions}
                value={settings.density}
                name="density"
                on-change={parent.onOptionChange}></ui-select>
        </div>
    </div>

    <div class="row">
        <div class="col m5 s12 input-label">
            {_("opts.highContrast")}
        </div>
        <div class="col m7 s12">
                <ui-switch
                    riot-value={settings.highcontrast}
                    name="highcontrast"
                    on-change={parent.onOptionChange}></ui-switch>
        </div>
    </div>


    <virtual if={isFullAccount}>
        <div class="row">
            <div class="col m5 s12 input-label">
                {_("opts.cookies")}
            </div>
            <div class="col m7 s12 input-label">
                <a onclick={onCookieSettingsClick}
                        class="link">{_("open")}</a>
            </div>
        </div>

        <div class="row">
            <div class="col m5 s12 input-label">
                {_("reset")}
            </div>
            <div class="col m7 s12 input-label">
                <a id="btnResetSettings" class="link" disabled={isResetDisabled} onclick={onReset}>{_("opts.resetLabel")}</a>
            </div>
        </div>
    </virtual>

    <script>
        const {SettingsStore} = require("core/SettingsStore.js")
        const {Localization} = require('core/Localization.js')
        const {LocalizationMeta} = require('core/Meta/Localization.meta.js')
        const {Auth} = require("core/Auth.js")
        this.isFullAccount = Auth.isFullAccount()
        this.email = Auth.getEmail()

        refreshAttributes(){
            this.settings = SettingsStore.getAll()
            this.isResetDisabled = !SettingsStore.hasUserSettings()
        }
        this.refreshAttributes()

        this.densityOptions = ["low", "medium", "high"].map((density) => {
            return {
                value: density,
                label: _(density)
            }
        })

        this.languageOptions = LocalizationMeta.langs.sort((a, b) => {
            return a.labelEn.localeCompare(b.labelEn)
        }).map((lang) => {
            return {
                value: lang.id,
                label: lang.labelEn + " (" + lang.label + ")"
            }
        })

        onLanguageChange(language){
            SettingsStore.changeSettings({
                language: language
            })
        }

        onLexonomyChangeEmail(email){
            SettingsStore.changeSettings({
                lexonomyEmail: email
            })
        }

        onLexonomyChangeApiKey(key){
            SettingsStore.changeSettings({
                lexonomyApiKey: key
            })
        }

        onCookieSettingsClick(evt){
            evt.preventUpdate = true
            window.SkE_CookieConsent.openSettings()
        }

        onReset(){
            if(!this.isResetDisabled){
                Dispatcher.trigger("openDialog", {
                    title: _("resetSettings"),
                    content: _("resetSettingsWarn"),
                    small: true,
                    buttons: [{
                        label: _("reset"),
                        class: "btn-primary",
                        onClick: (dialog, modal) => {
                            SettingsStore.resetSettings()
                            modal.close()
                        }
                    }]
                })
            }
        }

        this.on("update", this.refreshAttributes)
    </script>
</settings-dialog-general>



<settings-dialog class="settings-dialog">
    <h4>{_('settings')}</h4>
    <small style="opacity: 0.6; position: relative; top:-10px;">{savingMsg}&nbsp;</small>
    <div class="content">
        <div class="row dense relative">
            <div class="col m9 s12">
                <settings-dialog-general class="settingsSection"></settings-dialog-general>
            </div>
        </div>
    </div>

    <script>
        require("./settings-dialog.scss")
        const {SettingsStore} = require("core/SettingsStore.js")

        onOptionChange(value, name){
            SettingsStore.changeSettings({
                [name]: value,
                noToast: true
            })
            if(this.isFullAccount){
                this.savingMsg = _("saving")
                this.update()
            }
        }

        settingsSaved(){
            this.savingMsg = _("opts.allSaved")
            clearTimeout(this.handle)
            this.handle = setTimeout(function(){
                this.savingMsg = ""
                this.mounted && this.update()
            }.bind(this), 5000)
            this.update()
        }

        this.on("update", this.refreshAttributes)

        this.on("mount", () => {
            SettingsStore.on("settingsSaved", this.settingsSaved)
            SettingsStore.on("change", this.update)
        })

        this.on("unmount", () => {
            SettingsStore.off("change", this.update)
            SettingsStore.off("settingsSaved", this.settingsSaved)
        })
    </script>
</settings-dialog>
