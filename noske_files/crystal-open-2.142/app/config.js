window.config = {
    URL_BONITO: "http://localhost/bonito/run.cgi/",
    // URL of endpoint for registering new users (e.g bonito/registration.cgi). Leave empty to disable registration.
    URL_REGISTER_NEW_USER: "",
    // Default language of the interface.
    DEFAULT_LOCALE: "en",
    // If true, plain image is rendered instead of YouTube iframe.
    DISABLE_EMBEDDED_YOUTUBE: false,
    // If true, Word Sketch, Word Sketch Difference, Thesaurus, Terms and Ngrams are not available.
    NO_SKE: true,
    // Set to true, if Corpus architect is not available. Some request will be send to Bonito instead of CA.
    NO_CA: true,
    // If true, corpus building is not available.
    READ_ONLY: false,
    // Message to be shown if READ_ONLY is true.
    READ_ONLY_MSG: "",
    // If not empty, dismissible notification message will be displayed in the top of the screen.
    NOTIFICATION: "",
    // URL to custom .css file to modify interface appearance.
    CUSTOM_STYLE: "",
    // URL of custom localization strings in .json file to change texts in the interface.
    // One URL per language is allowed, e.g.: CUSTOM_LOCALE_EN, CUSTOM_LOCALE_DE, CUSTOM_LOCALE_IT,...
    CUSTOM_LOCALE_EN: "",
    // Remove SkE advertisement banner from dashboard.
    HIDE_DASHBOARD_BANNER: true,

    links: {
        "wl_download_limits": "https://www.sketchengine.eu/guide/access-to-unlimited-wordlists/",
        "priceList": "https://www.sketchengine.eu/price-list/",
        "quickStartGuide": "https://www.sketchengine.eu/quick-start-guide/",
        "userGuide": "https://www.sketchengine.eu/user-guide/",
        "sketchEngineIntro": "https://www.youtube.com/embed/f4eszLB47Qk",
        "cqlIntro": "https://www.youtube.com/embed/nOMr_D6ISRM",
        "concordanceBasicVideo": "https://www.youtube.com/embed/FzI6tbO5EvQ",
        "youtubeChannel": "https://www.youtube.com/channel/UCo2fn2_SNxCikCSAFCBcWBw",
        "privacyPolicy": "https://www.sketchengine.eu/gdpr-privacy-consent/",
        "serviceRequest": "https://www.lexicalcomputing.com/request-language-data-or-services/",
        "globalAdministration": "",
        "parallelCorporaFileFormats" : "https://www.sketchengine.eu/guide/setting-up-parallel-corpora/",
        "supportMail": "support@sketchengine.eu",
        "bootCamp": "https://www.sketchengine.eu/bootcamp/",
        "cqlManual": "https://www.sketchengine.eu/documentation/corpus-querying/",
        "regexManual": "https://www.sketchengine.eu/guide/regular-expressions/",
        "updateBrowser": "https://browsehappy.com/",
        "compareCorpora": "https://www.sketchengine.eu/guide/compare-corpora/",
        "multiLingualCorpora": "https://www.sketchengine.eu/guide/setting-up-parallel-corpora/",
        "accountLimitations": "https://www.sketchengine.eu/guide/account-limitations/",
        "fupInfo": "https://www.sketchengine.eu/fair-use-policy/",
        "h_lemma": " https://www.sketchengine.eu/my_keywords/lemma/",
        "h_collocate": " https://www.sketchengine.eu/my_keywords/collocate/",
        "h_subcorpus": "https://www.sketchengine.eu/my_keywords/subcorpus/",
        "h_frequency": "https://www.sketchengine.eu/my_keywords/frequency/",
        "h_wordForm": "https://www.sketchengine.eu/my_keywords/word-form/",
        "h_subcorpus": "https://www.sketchengine.eu/my_keywords/subcorpus/",
        "h_regex": "https://www.sketchengine.eu/guide/regular-expressions/",
        "h_token": "https://www.sketchengine.eu/my_keywords/token/",
        "h_KWIC": "https://www.sketchengine.eu/my_keywords/kwic/",
        "h_attribute": "https://www.sketchengine.eu/my_keywords/positional-attribute/",
        "h_lc": "https://www.sketchengine.eu/my_keywords/lc/",
        "h_tag": "https://www.sketchengine.eu/my_keywords/tag/",
        "h_lempos": "https://www.sketchengine.eu/my_keywords/lempos/",
        "h_structure": "https://www.sketchengine.eu/my_keywords/structure/",
        "h_annotating": "https://www.sketchengine.eu/guide/annotating-corpus-text/",
        "h_relfreq": "https://www.sketchengine.eu/my_keywords/freqmill/",
        "h_cqlManual": "https://www.sketchengine.eu/documentation/corpus-querying/",
        "cb_basics": "https://www.sketchengine.eu/documentation/cql-basics/",
        "cb_structures": "https://www.sketchengine.eu/documentation/cql-search-structures/",
        "cb_within_containing": "https://www.sketchengine.eu/documentation/cql-within-containing/",
        "cb_meet": "https://www.sketchengine.eu/documentation/cql-meet-union/",
        "cb_wordsketch": "https://www.sketchengine.eu/documentation/cql-word-sketches/",
        "cb_thesaurus": "https://www.sketchengine.eu/documentation/cql-thesaurus/",
        "cb_global_conditions": "https://www.sketchengine.eu/documentation/cql-global-conditions/",
        "academicSubscription": "https://www.sketchengine.eu/academic-and-non-academic-subscriptions/"
    }
}
