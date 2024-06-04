const Meta = {
    operators:{
        AND: 1,
        OR: 2
    },
    filterList: {
        "basic": ["all", "startingWith", "endingWith", "containing"],
        "advanced": ["all", "startingWith", "endingWith", "containing", "regex", "fromList"]
    },
    filters: {
        "all": {
            value: "all",
            labelId: "all",
            regex: ".*"
        },
        "startingWith": {
            value: "startingWith",
            labelId: "startingWith",
            regex: "{key}.*",
            keyword: true
        },
        "endingWith": {
            value: "endingWith",
            labelId: "endingWith",
            regex: ".*{key}",
            keyword: true
        },
        "containing": {
            value: "containing",
            labelId: "containing",
            regex: ".*{key}.*",
            keyword: true
        },
        "regex": {
            value: "regex",
            labelId: "matchingRegex",
            regex: "{key}",
            keyword: true
        },
        "fromList": {
            value: "fromList",
            labelId: "fromList",
            regex: "{key}"
        }
    },

    wlnumsList: [{
        labelId: "frequency",
        value: "frq",
        tooltip: "t_id:frequency"
    },{
        labelId: "wl.freqcls",
        value: "freqcls",
        tooltip: "t_id:freqcls"
    },{
        labelId: "relfreq",
        value: "relfreq",
        tooltip: "t_id:relfreq"
    }, {
        labelId: "wl.docf",
        value: "docf",
        tooltip: "t_id:docf"
    }, {
        labelId: "reldocf",
        value: "reldocf",
        tooltip: "t_id:reldocf"
    }, {
        label: "ARF",
        value: "arf",
        tooltip: "t_id:arf"
    }, {
        label: "ALDF",
        value: "aldf",
        tooltip: "t_id:aldf"
    }],

    viewAsOptions: [{
        value: 1,
        labelId: "wl.simpleList",
        tooltip: "t_id:wl_a_simple_list"
    }, {
        value: 2,
        labelId: "wl.displayAs",
        tooltip: "t_id:wl_a_display_as"
    }]
}

module.exports = Meta




