const path = require('path')

module.exports = {
	entry: './static/dashb/dock3.ts',
	//entry: './static/dummy.ts',
	//entry: './static/jobs/chains.ts',
	output: {
		filename: 'dock3_bundle.js',
		//filename: 'dummy_bundle.js',
		//filename: 'chains_bundle.js',
		path: path.resolve(__dirname, 'static', 'dashb')
		//path: path.resolve(__dirname, 'static', 'jobs')
		//path: path.resolve(__dirname, 'static')
	},
	module: {
		rules: [
			{
				test: /\.html$/,
				use: [
					'html-loader'
				]
			},
			{
				test: /\.scss$/,
				use: [
					'css-loader',
					'sass-loader'
				]
			},
			{
				test: /\.ts$/,
				use: 'ts-loader',
			},
		]
	},
	resolve: {
		extensions: ['.ts', '.js'],
	}
};
