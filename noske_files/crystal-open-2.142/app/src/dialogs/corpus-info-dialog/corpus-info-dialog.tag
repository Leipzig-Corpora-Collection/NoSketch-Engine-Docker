<corpus-info-dialog class="corpus-info-dialog relative">
    <div if={!corpus}>
        <preloader-spinner overlay=1></preloader-spinner>
    </div>
    <div if={corpus && !error}>
        <div class="titleWithButton">
            <span class="title">
                <span class="mr-4">
                    <h4>{corpus.name}</h4>
                    <i if={!window.config.NO_CA && opts.corpname == actualCorpname && corpus.user_can_manage}
                            class="material-icons material-clickable"
                            onclick={onCorpusEditClick}>edit</i>
                </span>
                <span class="corpname grey-text hide-on-med-and-down">
                    {corpus.corpname}
                    <span if={corpusListData && corpusListData.created}>
                        ● {_("created")}
                        {window.Formatter.date(new Date(corpusListData.created), {
                                year: "numeric",
                                month: "long",
                                day: "numeric",
                                hour: "numeric",
                                minute: "numeric",
                                second: "numeric"
                            })}
                    </span>
                </span>
            </span>
        </div>
        <div if={corpus.info} class="grey-text">
            {corpus.info}
            <a if={corpus.infohref} href={corpus.infohref} target="_blank">{_("seeMore")}</a>
        </div>
        <div class="mt-3 mb-2 buttons">
            <a if={window.permissions.ca}
                    href="#ca?corpname={corpus.corpname}"
                    class="btn white-text"
                    onclick={closeDialog}>
                {_("manageCorpus")}
            </a>
            <a href="#ca-subcorpora"
                    class="btn">
                {_("ca.subcorporaDesc")}
            </a>
            <a if={window.permissions["compare-corpora"]}
                    href="#compare-corpora?corpname={corpus.corpname}"
                    class="btn tooltipped"
                    data-tooltip={_("compareCorporaDesc")}>
                {_("compareCorpora")}
            </a>
            <a href="#text-type-analysis?corpname={corpus.corpname}&wlminfreq=1&include_nonwords=1&showresults=1&wlicase=1&wlnums=frq"
                    class="btn"
                    onclick={closeDialog}>
                {_("tta")}
            </a>
        </div>

        <div class="colsContainer {hasRightCol: activeRequest || (structures && structures.length)}">
            <div class="leftCol">
                <div class="corpInfoSections">
                    <div>
                        <div class="card-panel generalInfo">
                            <h5>{_("ci.generalInfo")}</h5>
                            <div>
                                <b>
                                    {_("language")}: {corpus.language_name}
                                </b>
                            </div>
                            <div>
                                <a href={corpus.infohref} class="btn" target="_blank">{_("corpusDescAndBibliography")}</a>
                            </div>
                            <div>
                                <a href={corpus.tagsetdoc} class="btn {disabled: !corpus.tagsetdoc}" target="_blank">{_(corpus.tagsetdoc ? "tagset" : "noTagset")}</a>
                            </div>
                            <div if={corpus.errsetdoc}>
                                <a href={corpus.errsetdoc} class="btn" target="_blank">{_("listCodes")}</a>
                            </div>
                        </div>
                    </div>

                    <div>
                        <div if={corpus.sizes}  class="counts card-panel">
                            <h5>{_("ci.counts")}&nbsp;<i class="material-icons tooltipped" data-tooltip="t_id:ci_counts">info</i></h5>
                            <table class="table">
                                <tr each={obj, idx in sizesList} if={corpus.sizes[obj[0]] > 0}>
                                    <td>
                                        <span class={tooltipped : !!obj[2]} data-tooltip={obj[2]}>
                                            {_(obj[1])}<sup if={obj[2]}>?</sup>
                                        </span>
                                    </td>
                                    <td class="right-align">{window.Formatter.num(parent.corpus.sizes[obj[0]])}</td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <div>
                        <div if={activeRequest || (attributes && attributes.length)} class="lexiconSizes card-panel">
                            <h5>{_("ci.lexiconSizes")}&nbsp;<i class="material-icons tooltipped" data-tooltip="t_id:ci_lexicon_sizes">info</i></h5>
                            <preloader-spinner small=1 if={activeRequest}></preloader-spinner>
                            <table if={!activeRequest} class="table">
                                <tr each={attr in attributes}>
                                    <td>
                                        <span if={attr.name == "word"} class="tooltipped" data-tooltip="t_id:ci_nonwords">
                                            word<sup>?</sup>
                                        </span>
                                        <span if={attr.name == "lempos"} class="tooltipped" data-tooltip="t_id:ci_lempos">
                                            lempos<sup>?</sup>
                                        </span>
                                        <span if={!["word", "lempos"].includes(attr.name)}>
                                            {attr.name}
                                        </span>
                                        <i if={attr.label} class="material-icons tooltipped" data-tooltip={attr.label}>info_outline</i>
                                    </td>
                                    <td class="right-align">{isNaN(attr.id_range) ? "" : window.Formatter.num(attr.id_range)}</td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <div>
                        <div if={corpus.wposlist && corpus.wposlist.length} class="card-panel">
                            <h5>{_("commonTags")}</h5>
                            <table class="table">
                                <tr each={pos in corpus.wposlist}>
                                    <td>{pos.label}</td>
                                    <td class="right-align"
                                            style="word-break: break-all;">{pos.value}</td>
                                </tr>
                            </table>
                            <a if={corpus.tagsetdoc}
                                    href="{corpus.tagsetdoc}"
                                    target="_blank"
                                    style="margin-top: 5px; display: inline-block;">
                                <i class="material-icons small-help" style="vertical-align: middle;">help_outline</i>
                                {_("moreInfo")}
                            </a>
                        </div>
                    </div>

                    <div>
                        <div if={corpus.lposlist && corpus.lposlist.length} class="card-panel t_lemposSuffixes">
                            <h5>{_("ci.lemposSuffixes")}&nbsp;<i class="material-icons tooltipped" data-tooltip="t_id:ci_lempos_suffixes">info</i></h5>
                            <table class="table">
                                <tr each={pos in corpus.lposlist}>
                                    <td>{pos.label}</td>
                                    <td class="right-align">{pos.value}</td>
                                </tr>
                            </table>
                        </div>
                    </div>


                    <div>
                        <div if={activeRequest || (subcorpora && subcorpora.length)} class="subcorpora card-panel">
                            <h5>{_("ci.subcorporaStatistics")}</h5>
                            <preloader-spinner small=1 if={activeRequest}></preloader-spinner>
                            <table if={!activeRequest} class="table">
                                <thead>
                                    <tr>
                                        <th>{_("subcorpus")}</th>
                                        <th>{_("tokens")}</th>
                                        <th>%</th>
                                    </tr>
                                </thead>
                                <tr each={sc in subcorpora}>
                                    <td>{sc.name}</td>
                                    <td class="right-align">{window.Formatter.num(sc.tokens)}</td>
                                    <td class="right-align">{window.Formatter.num(sc.relsize,  {minimumFractionDigits: 2})}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <div if={activeRequest || (structures && structures.length)} class="rightCol t_textTypes">
                <div class="card-panel noPaddingCard">
                    <h5>{_("textTypes")}
                        &nbsp;
                        <i class="material-icons tooltipped" data-tooltip="t_id:ci_text_types">info</i>
                        <a href="#text-type-analysis?corpname={corpus.corpname}&wlminfreq=1&include_nonwords=1&showresults=1&wlicase=1&wlnums=frq"
                                class="btn btn-flat right"
                                onclick={closeDialog}>
                                {_("tta")}
                        </a>
                    </h5>
                    <preloader-spinner small=1 if={activeRequest}></preloader-spinner>
                    <ul if={!activeRequest} class="collapsible" data-collapsible="expandable">
                        <li each={struct, idx in structures} class={active: idx == 0}>
                            <div class="collapsible-header">
                                <span class="t_structName"><{struct.name}> {struct.label}</span>
                                <span class="scnt">({struct.attributes.length})</span>
                                <span class="right">{window.Formatter.num(struct.size)}</span>
                            </div>
                            <div class="collapsible-body">
                                <i if={!struct.attributes.length} class="grey-text">
                                    {_("structWithoutAttributes")}
                                </i>
                                <div each={attr in struct.attributes}>
                                    <span class="t_attrName">{attr.label || attr.name}</span>
                                    , &nbsp;
                                    <span class="attr">{struct.name}.{attr.name}</span>
                                    <span class="right">{window.Formatter.num(attr.size)}</span>
                                    <a href={getTextTypeAnalysisUrl(struct.name + "." + attr.name)}
                                            class="tooltipped"
                                            data-tooltip={_("statsWholeCorp")}
                                            onclick={closeDialog}>
                                        <i class="material-icons rotate90CW">insert_chart</i>
                                    </a>
                                </div>
                            </div>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <div if={error}>
        <div class="error">{_("error")}: {error}</div>
    </div>

    <script>
        require('./corpus-info-dialog.scss')
        const {Connection} = require("core/Connection.js")
        const {Url} = require('core/url.js')
        const {AppStore} = require('core/AppStore.js')
        const {Auth} = require('core/Auth.js')
        const Dialogs = require('dialogs/dialogs.js')

        this.mixin("tooltip-mixin")

        this.activeRequest = null
        this.isFullAccount = Auth.isFullAccount()
        this.corpusListData = AppStore.getCorpusByCorpname(this.opts.corpname)
        this.actualCorpname = AppStore.getActualCorpname()

        if (this.opts.corpname == this.actualCorpname) {
            this.corpus = AppStore.getActualCorpus()
        } else {
            this.corpus = {}
            AppStore.loadAnyCorpus(this.opts.corpname)
        }

        this.sizesList = [
            ["tokencount", "tokens"],
            ["wordcount", "wordP"],
            ["sentcount", "sentences"],
            ["parcount", "paragraphs"],
            ["doccount", "documents"]
        ]

        getTextTypeAnalysisUrl(wlattr){
            return Url.create("text-type-analysis", {
                corpname: this.opts.corpname,
                wlminfreq: 1,
                wlicase: true,
                include_nonwords: true,
                showresults: true,
                wlnums: "frq",
                wlattr: wlattr
            })
        }

        load(){
            this.error = null
            if(this.activeRequest){
                Connection.abortRequest(activeRequest)
            }
            this.activeRequest = Connection.get({
                url: window.config.URL_BONITO + "corp_info",
                data: {
                    corpname: opts.corpname,
                    struct_attr_stats: true,
                    subcorpora: true
                },
                done: this.onLoad,
                fail: this.onFail
            })

            this.update()
        }

        onLoad(payload){
            if(this.isMounted){ // user could close dialog before loaded
                if(payload.error){
                    this.error = payload.error
                } else {
                    this.attributes = payload.attributes
                    this.structures = payload.structures.sort((a, b) => {return b.attributes.length - a.attributes.length})
                    this.structures.forEach(s => {
                        s.attributes.sort((a,b) => {return (a.label || a.name).localeCompare(b.label || b.name)})
                    })
                    this.subcorpora = payload.subcorpora
                }
                this.activeRequest = null
                this.update()
            }
        }

        onFail(error){
            this.error = error
            this.activeRequest = null
            this.update()
        }

        onCorpusEditClick(){
            Dialogs.showCorpusConfigDialog(this.corpus.id)
        }

        closeDialog(){
            Dispatcher.trigger("closeDialog", "corpusInfo")
        }

        showGrammarDialog(is_term){
            Dialogs.showGrammarDetailDialog({corpname: this.corpus.corpname, is_term: is_term})
        }

        onCorpusLoaded(corpus){
            this.corpus = corpus
            this.update()
        }

        Dispatcher.on('ANY_CORPUS_LOADED', this.onCorpusLoaded.bind(this))

        this.on("mount", () => {
            this.load()
            Url.updateQuery({corp_info: 1})
            Dispatcher.on("CORPUS_INFO_LOADED", this.onCorpusLoaded)
        })

        this.on("unmount", () => {
            let query = Url.getQuery()
            delete query.corp_info
            Url.setQuery(query)
            Dispatcher.off("CORPUS_INFO_LOADED", this.onCorpusLoaded)
        })

        this.on("updated", () => {
            $('.collapsible', this.root).collapsible()
            $('.tooltipped', this.root).tooltip({
                enterDelay: 500
            })
        })

    </script>
</corpus-info-dialog>
