new vUnit({
    CSSMap: {
        // The selector (VUnit will create rules ranging from .selector1 to .selector100)
        '.vh_height': {
            // The CSS property (any CSS property that accepts px as units)
            property: 'height',
            // What to base the value on (vh, vw, vmin or vmax)
            reference: 'vh'
        },
        // Wanted to have a font-size based on the viewport width? You got it.
        '.vw_font-size': {
            property: 'font-size',
            reference: 'vw'
        },
        // vmin and vmax can be used as well.
        '.vmin_margin-top': {
            property: 'margin-top',
            reference: 'vmin'
        },
        '.vmin_margin-bottom': {
            property: 'margin-bottom',
            reference: 'vmin'
        }
    },
    onResize: function() {
        console.log('A screen resize just happened, yo.');
    }
}).init(); // call the public init() method