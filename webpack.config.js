const path = require('path');

// A function, to give the mode (development or production) to Babel : its react preset compiles the JSX
// for the runtime of the same mode, which webpack then chooses
module.exports = (env, argv) => ({
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
		  options: { envName: argv.mode },
		}
	  }, {
        test: /\.css$/,
		include: path.resolve(__dirname, 'frontend/src'),
        use: [ 'style-loader', 'css-loader' ]
      }, {
		test: /\.scss$/,
		include: path.resolve(__dirname, 'frontend/src'),
		use: [
			"style-loader", // creates style nodes from JS strings
			"css-loader", // translates CSS into CommonJS
			{
				loader: "sass-loader", // compiles Sass to CSS
				// No deprecation warnings for the stylesheets of node_modules (bootstrap), only for ours
				options: { sassOptions: { quietDeps: true } },
			},
		]
	  }, {
		test: /\.(gif|png|jpe?g|svg|ico)$/i,
		include: path.resolve(__dirname, 'frontend/src/images'),
		type: 'asset/resource',
		generator: {
			// In frontend/static/images, with their path in frontend/src/images
			filename: (pathData) => path.posix.join(
				'../images', path.relative('frontend/src/images', path.dirname(pathData.filename)), '[name][ext]'
			),
		},
	  }, {
		// Model files to download in the tutorials, in frontend/static/tutorials
		test: /\.(bnd|cfg)$/i,
		include: path.resolve(__dirname, 'frontend/src/tutorials'),
		type: 'asset/resource',
		generator: {
			filename: (pathData) => path.posix.join(
				'../tutorials', path.relative('frontend/src/tutorials', path.dirname(pathData.filename)), '[name][ext]'
			),
		},
	  }
	]
  },
   optimization: {
    minimize: true,
	},
  devtool: 'source-map',
  entry: './frontend/src/index.js',
  output: {
	path: path.resolve(__dirname, "frontend/static/js"),
	filename: 'index.js',
	chunkFilename: '[name].js',
	// Without the bundles of previous builds
	clean: true,
  },
});
