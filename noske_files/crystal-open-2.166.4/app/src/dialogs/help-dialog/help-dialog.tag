<help-help-tab>
    <screen-overlay is-loading={isSending}></screen-overlay>
    <br>
    <div if={!showForm} class="center-align cardBtnContainer">
        <a href={externalLink("quickStartGuide")} target="_blank">
            <div class="cardBtn card-panel">
                <i class="material-icons">explore</i>
                <div class="title">{_("hp.startGuideTitle")}</div>
                <div class="desc">{_("hp.startGuideDesc")}</div>
            </div>
        </a>

        <a href={externalLink("userGuide")} target="_blank">
            <div class="cardBtn card-panel">
                <i class="material-icons">help</i>
                <div class="title">{_("hp.userGuideTitle")}</div>
                <div class="desc">{_("hp.userGuideDesc")}</div>
            </div>
        </a>

        <a href="javascript:void(0);" onclick={onShowIntro}>
            <div class="cardBtn card-panel">
                <i class="material-icons">featured_video</i>
                <div class="title">{_("hp.showIntro")}</div>
                <div class="desc">{_("hp.showIntroDesc")}</div>
            </div>
        </a>

        <a href="{config.links.bibliographyOfSke}" target="_blank">
            <div class="cardBtn card-panel">
                <i class="material-icons">library_books</i>
                <div class="title">{_("hp.bibliographyTitle")}</div>
                <div class="desc">{_("hp.bibliographyDesc")}</div>
            </div>
        </a>

        <a if={news.length}
                href="javascript:void(0);"
                onclick={onWhatsNewClick}>
            <div class="cardBtn card-panel">
                <i class="material-icons">new_releases</i>
                <div class="title">{_("whatsNew")}</div>
                <div class="desc">{_("hp.whatsNewDesc")}</div>
            </div>
        </a>
    </div>

    <script>
        const {intros} = require("common/wizards.js")
        const {Auth} = require("core/Auth.js")
        const {WhatsNew} = require("misc/whats-new/whatsnew.js")

        this.showForm = false
        this.isSending = false
        this.isFullAccount = Auth.isFullAccount()
        this.news = WhatsNew.getAllNewsList()

        toggleForm(show){
            this.showForm = show
        }

        onShowIntro(){
            this.parent.parent.modalParent.close()
            Dispatcher.trigger("ROUTER_GO_TO", "corpus", {tab: "basic"})
            setTimeout(() => {
                intros["newui"].start()
            }, 1000)
        }

        onWhatsNewClick(){
            WhatsNew.openDialog()
        }
    </script>
</help-help-tab>


<help-video-tab>
    <br>
    <div class="videoContainer">
        <div class="videoLeftCol">
            <div class="colHeader">{_("hp.videoStarting")}</div>
            <br>
            <div class="youtubeVideoContainer">
                <a if={window.config.DISABLE_EMBEDDED_YOUTUBE}
                        href={externalLink("sketchEngineIntro")}
                        target="_blank"
                        class="youtubePlaceholder"
                        style="width:560px;height:315px;">
                    <img src="images/youtube-placeholder.jpg"
                            loading="lazy"
                            alt="Sketch Engine intro">
                </a>
                <iframe if={!window.config.DISABLE_EMBEDDED_YOUTUBE}
                        width="560"
                        height="315"
                        src={externalLink("sketchEngineIntro")}
                        frameborder="0"
                        allow="autoplay; encrypted-media"
                        allowfullscreen
                        loading="lazy"></iframe>
            </div>
        </div>
        <div class="videoRightCol">
            <div class="colHeader">{_("videoLessons")}</div>
            <br>
            {_("hp.youtube1")}<a href={externalLink("youtubeChannel")} target="_blank">{_("hp.youtube2")}</a>
            <br><br>
            <div>
                <a href={externalLink("youtubeChannel")} target="_blank">
                    <svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
                         viewBox="0 0 380.9 85" xml:space="preserve" style="width: 140px;">
                        <g>
                            <path class="help-youtube-st0" d="M118.9,13.3c-1.4-5.2-5.5-9.3-10.7-10.7C98.7,0,60.7,0,60.7,0s-38,0-47.5,2.5C8.1,3.9,3.9,8.1,2.5,13.3
                                C0,22.8,0,42.5,0,42.5s0,19.8,2.5,29.2c1.4,5.2,5.5,9.3,10.7,10.7C22.8,85,60.7,85,60.7,85s38,0,47.5-2.5
                                c5.2-1.4,9.3-5.5,10.7-10.7c2.5-9.5,2.5-29.2,2.5-29.2S121.5,22.8,118.9,13.3z"/>
                            <polygon class="help-youtube-st1" points="48.6,60.7 80.2,42.5 48.6,24.3  "/>
                        </g>
                        <g>
                            <g>
                                <path class="help-youtube-st2" d="M176.3,77.4c-2.4-1.6-4.1-4.1-5.1-7.6c-1-3.4-1.5-8-1.5-13.6v-7.7c0-5.7,0.6-10.3,1.7-13.8
                                    c1.2-3.5,3-6,5.4-7.6c2.5-1.6,5.7-2.4,9.7-2.4c3.9,0,7.1,0.8,9.5,2.4c2.4,1.6,4.1,4.2,5.2,7.6c1.1,3.4,1.7,8,1.7,13.8v7.7
                                    c0,5.7-0.5,10.2-1.6,13.7c-1.1,3.4-2.8,6-5.2,7.6c-2.4,1.6-5.7,2.4-9.8,2.4C182.1,79.8,178.7,79,176.3,77.4z M189.8,69
                                    c0.7-1.7,1-4.6,1-8.5V43.9c0-3.8-0.3-6.6-1-8.4c-0.7-1.8-1.8-2.6-3.5-2.6c-1.6,0-2.8,0.9-3.4,2.6c-0.7,1.8-1,4.6-1,8.4v16.6
                                    c0,3.9,0.3,6.8,1,8.5c0.6,1.7,1.8,2.6,3.5,2.6C188,71.6,189.1,70.8,189.8,69z"/>
                                <path class="help-youtube-st2" d="M360.9,56.3V59c0,3.4,0.1,6,0.3,7.7c0.2,1.7,0.6,3,1.3,3.7c0.6,0.8,1.6,1.2,3,1.2c1.8,0,3-0.7,3.7-2.1
                                    c0.7-1.4,1-3.7,1.1-7l10.3,0.6c0.1,0.5,0.1,1.1,0.1,1.9c0,4.9-1.3,8.6-4,11s-6.5,3.6-11.4,3.6c-5.9,0-10-1.9-12.4-5.6
                                    c-2.4-3.7-3.6-9.4-3.6-17.2v-9.3c0-8,1.2-13.8,3.7-17.5c2.5-3.7,6.7-5.5,12.6-5.5c4.1,0,7.3,0.8,9.5,2.3c2.2,1.5,3.7,3.9,4.6,7
                                    c0.9,3.2,1.3,7.6,1.3,13.2v9.1H360.9z M362.4,33.9c-0.6,0.8-1,2-1.2,3.7c-0.2,1.7-0.3,4.3-0.3,7.8v3.8h8.8v-3.8
                                    c0-3.4-0.1-6-0.3-7.8c-0.2-1.8-0.7-3-1.3-3.7c-0.6-0.7-1.6-1.1-2.8-1.1C363.9,32.7,363,33.1,362.4,33.9z"/>
                                <path class="help-youtube-st2" d="M147.1,55.3L133.5,6h11.9l4.8,22.3c1.2,5.5,2.1,10.2,2.7,14.1h0.3c0.4-2.8,1.3-7.4,2.7-14l5-22.4h11.9
                                    L159,55.3v23.6h-11.8V55.3z"/>
                                <path class="help-youtube-st2" d="M241.6,25.7v53.3h-9.4l-1-6.5h-0.3c-2.5,4.9-6.4,7.4-11.5,7.4c-3.5,0-6.1-1.2-7.8-3.5
                                    c-1.7-2.3-2.5-5.9-2.5-10.9V25.7h12v39.1c0,2.4,0.3,4.1,0.8,5.1c0.5,1,1.4,1.5,2.6,1.5c1,0,2-0.3,3-1c1-0.6,1.7-1.4,2.1-2.4V25.7
                                    H241.6z"/>
                                <path class="help-youtube-st2" d="M303.1,25.7v53.3h-9.4l-1-6.5h-0.3c-2.5,4.9-6.4,7.4-11.5,7.4c-3.5,0-6.1-1.2-7.8-3.5
                                    c-1.7-2.3-2.5-5.9-2.5-10.9V25.7h12v39.1c0,2.4,0.3,4.1,0.8,5.1c0.5,1,1.4,1.5,2.6,1.5c1,0,2-0.3,3-1c1-0.6,1.7-1.4,2.1-2.4V25.7
                                    H303.1z"/>
                                <path class="help-youtube-st2" d="M274.2,15.7h-11.9v63.2h-11.7V15.7h-11.9V6h35.5V15.7z"/>
                                <path class="help-youtube-st2" d="M342.8,34.2c-0.7-3.4-1.9-5.8-3.5-7.3c-1.6-1.5-3.9-2.3-6.7-2.3c-2.2,0-4.3,0.6-6.2,1.9
                                    c-1.9,1.2-3.4,2.9-4.4,4.9h-0.1l0-28.1h-11.6v75.6h9.9l1.2-5h0.3c0.9,1.8,2.3,3.2,4.2,4.3c1.9,1,3.9,1.6,6.2,1.6
                                    c4.1,0,7-1.9,8.9-5.6c1.9-3.7,2.9-9.6,2.9-17.5v-8.4C343.8,42.2,343.5,37.5,342.8,34.2z M331.8,55.9c0,3.9-0.2,6.9-0.5,9.1
                                    c-0.3,2.2-0.9,3.8-1.6,4.7c-0.8,0.9-1.8,1.4-3,1.4c-1,0-1.9-0.2-2.7-0.7c-0.8-0.5-1.5-1.2-2-2.1V38.1c0.4-1.4,1.1-2.6,2.1-3.6
                                    c1-0.9,2.1-1.4,3.2-1.4c1.2,0,2.2,0.5,2.8,1.4c0.7,1,1.1,2.6,1.4,4.8c0.3,2.3,0.4,5.5,0.4,9.6V55.9z"/>
                            </g>
                        </g>
                    </svg>
                </a>
            </div>
        </div>
    </div>
</help-video-tab>


<help-keyboard-tab>
    <br>
    <div class="noteBar background-color-blue-100">
        {_("hp.hotkeysDesc")}
    </div>
    <img src="images/hotkeys.gif" loading="lazy">
    <div each={feature, featureId in hotkeys} class="hotkeyFeature">
        <h4>{feature.label}</h4>
        <div each={hotkey in feature.bindings} if={!hotkey.hidden}>
            <span class="key">
                <raw-html content={this.parent.parent.getHotkeyShortcut(hotkey)}></raw-html>
            </span>
            <span class="action">
                <raw-html content={addFormatting(_(hotkey.help))}></raw-html>
            </span>
        </div>
    </div>

    <script>
        const {HotkeysMeta} = require("core/Meta/Hotkeys.meta.js")

        this.hotkeys = HotkeysMeta

        getHotkeyShortcut(hotkey){
            return hotkey.key.split(" ").map((key) => {
                return "<b>" + key + "</b>";
            }).join(" <small> " + _("hp.then") + " </small> ")
        }

        addFormatting(text){
            let open = false
            while(text.indexOf("**") != -1){
                text = text.replace("**", open ? "</b>" : "<b>")
                open = !open
            }
            if (open){
                text += "<b>"
            }
            return text
        }
    </script>
</help-keyboard-tab>



<help-dialog class="help-dialog">
    <ui-tabs active={opts.tab || "help"} tabs={tabs}></ui-tabs>

    <script>
        require("./help-dialog.scss")

        this.tabs = [{
            tabId: "help",
            labelId: "hp.helpAndSupport",
            tag: "help-help-tab"
        }, {
            tabId: "video",
            labelId: "videoLessons",
            tag: "help-video-tab"
        }, {
            tabId: "keyboard",
            labelId: "hp.keyboardShortcuts",
            tag: "help-keyboard-tab"
        }]
    </script>
</help-dialog>
