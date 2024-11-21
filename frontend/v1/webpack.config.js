const path = require("path");

const config = {
  devtool: "eval-source-map",
  entry: "./app/index.js",
  output: {
    path: path.resolve("../../server/static/js"),
    filename: "bundle.js",
    publicPath: "",
  },
  module: {
    rules: [
      {
        test: /\.m?js$/,
        resolve: {
          fullySpecified: false,
        },
      },
      {
        test: /\.m?js$/,
        exclude: /node_modules/,
        resolve: {
          fullySpecified: false,
        },
        use: ["babel-loader"],
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader?modules"],
      },
    ],
  },
};

module.exports = config;
