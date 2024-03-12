const CompressionPlugin = require("compression-webpack-plugin");
const TerserPlugin = require("terser-webpack-plugin");
const path = require('path');

module.exports = {
  module: {
	rules: [
	  {
		test: /\.jsx?$/,
		include: path.resolve(__dirname, 'frontend/src'),
		exclude: /node_modules/,
		resolve: {
			extensions: ['.js', '.jsx'],
  		},
		use: {
		  loader: "babel-loader",
		}
	  }, {
        test: /\.css$/,
		include: path.resolve(__dirname, 'frontend/src'),
        use: [ 'style-loader', 'css-loader' ]
      }, {
        test: /\.(eot|ttf|woff|woff2)$/,
		include: path.resolve(__dirname, 'frontend/src'),
        use:[{
			loader: 'file-loader?name=public/fonts/[name].[ext]'
		}]
	  }, {
		test: /\.scss$/,
		include: path.resolve(__dirname, 'frontend/src'),
		use: [
			"style-loader", // creates style nodes from JS strings
			"css-loader", // translates CSS into CommonJS
			"sass-loader" // compiles Sass to CSS, using Node Sass by default
		]
	  }, {
		test: /\.(gif|png|jpe?g|svg|ico)$/i,
		include: path.resolve(__dirname, 'frontend/src/images'),
  		use: [{
			loader: 'file-loader',
			options: {
				name: '[path][name].[ext]',
				context: 'frontend/src/images',
				outputPath: "../images/",
			},
		}]
	  }
	]
  },
   optimization: {
    minimize: true,
//     minimizer: [new TerserPlugin()],
//   	splitChunks: {
//       chunks: 'all',
	},
//   },
//   plugins: [
//     new CompressionPlugin({
// 		test: /\.js/
// 	})
//   ],
  devtool: 'source-map',
  entry: './frontend/src/index.js',
  output: {
	path: path.resolve(__dirname, "frontend/static/js"),
	// publicPath: "frontend/static/js/",
	filename: 'index.js',
	chunkFilename: '[name].js'
  },
};
