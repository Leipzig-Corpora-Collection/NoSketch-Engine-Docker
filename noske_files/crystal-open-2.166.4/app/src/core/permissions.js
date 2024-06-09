const {Auth} = require("core/Auth.js")
const {AppStore} = require("core/AppStore.js")


class PermissionsClass{
    constructor(){
        Dispatcher.on("AUTH_LOGIN", this.refresh.bind(this))
        Dispatcher.on("ON_LOGIN_AS_DONE", this.refresh.bind(this))
        AppStore.on("corpusChanged", this.refresh.bind(this))
        AppStore.on("corpusStatusChanged", this.refresh.bind(this))

        this.refresh()
    }

    refresh(){
        let isFA = Auth.isFullAccount()
        let isA = Auth.isAnonymous()
        let hasSkE = !window.config.NO_SKE
        let hasCA = !window.config.NO_CA
        let RO = window.config.READ_ONLY
        let corpus = AppStore.getActualCorpus()
        let canM = corpus && corpus.user_can_manage
        let canU = corpus && corpus.user_can_upload

        window.permissions = {
            'wordsketch':            hasSkE,
            'sketchdiff':            hasSkE,
            'thesaurus':             hasSkE,
            'concordance':           true,
            'parconcordance':        true,
            'wordlist':              true,
            'ngrams':                hasSkE,
            'keywords':              true,
            'trends':                true,
            'tta':                   true,
            'octerms':               hasSkE,
            'ocd':                   !isA && !RO && hasSkE,

            'ca':                    !RO && !isA,
            'ca-create':             isFA && !RO && hasCA,
            'ca-create-content':     isFA && !RO && hasCA && canM,
            'ca-create-compile':     isFA && !RO && hasCA && canM,
            'ca-compile':            isFA && !RO && hasCA && (canM || canU),
            'ca-alignment':          isFA && !RO && hasCA,
            'ca-upload-aligned':     isFA && !RO && hasCA,
            'ca-upload-nonaligned':  isFA && !RO && hasCA,
            'ca-settings-aligned':   isFA && !RO && hasCA,
            'ca-compile-nonaligned': isFA && !RO && hasCA,
            'ca-compile-aligned':    isFA && !RO && hasCA,
            'ca-add-content':        isFA && !RO && hasCA && (canM || canU),
            'ca-browse':             isFA && !RO && hasCA && (canM || canU),
            'ca-share':              isFA && !RO && hasCA && canM,
            'ca-subcorpora':         !RO && !isA,
            'ca-logs':               isFA && !RO && hasCA && canM,
            'ca-config':             isFA && !RO && hasCA && canM,

            'bgjobs':                !isA, // IP auth ?
            'my':                    !RO && hasCA && !isA, // IP auth ?
            'my-grammars':           !RO && hasCA && !isA,
            'compare-corpora':       hasCA // TODO -> to bonito

        }
    }
}

new PermissionsClass()
