import { WebpackOverrideFn } from "@remotion/cli";

export const webpackOverride: WebpackOverrideFn = (currentConfiguration) => {
  return {
    ...currentConfiguration,
    module: {
      ...currentConfiguration.module,
      rules: [
        ...(currentConfiguration.module?.rules || []),
        {
          test: /\.tsx?$/,
          loader: "ts-loader",
          options: {
            transpileOnly: true,
          },
        },
      ],
    },
    resolve: {
      ...currentConfiguration.resolve,
      extensions: [".ts", ".tsx", ".js", ".jsx"],
    },
  };
};