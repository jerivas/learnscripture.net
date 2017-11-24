var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')

module.exports = {
    context: __dirname,

    entry: './learnscripture/static/js/index', // entry point of our app, index.js

    output: {
        path: path.resolve(__dirname, 'learnscripture/static/webpack_bundles'),
        filename: "[name]-[hash].js"
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                use: [
                    'style-loader',
                    'css-loader'
                ]
            },
        ]
    },
    plugins: [
        new BundleTracker({filename: './webpack-stats.json'}),
        new webpack.ProvidePlugin({
            $: "jquery",
            jQuery: "jquery",
            "window.jQuery": "jquery",
        })
    ],
    resolve: {
        modules: [
            "node_modules",
            path.resolve(__dirname, 'learnscripture/static/bootstrap/js'),
            path.resolve(__dirname, 'learnscripture/static/js'),
        ],
        alias: {
            "jquery": "jquery/src/jquery",
        }
    }
}
