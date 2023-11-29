# auto-pr-writer
Automatically generate comprehensive Pull Request descriptions

This GitHub Action, `auto-pr-writer`, automates the creation of comprehensive and informative descriptions for your Pull Requests (PRs) based on the changes made in the PR.

## Features
- **Automatic Generation**: Upon opening a new PR, `auto-pr-writer` kicks in to generate a detailed description.
- **Customizable**: The generated text is customizable, allowing you to make adjustments after it's been added.
- **Time-Saving**: Reduces the manual effort required in crafting PR descriptions, especially for large changes.

## How It Works
When a new PR is opened in your repository, `auto-pr-writer` will be triggered. Approximately 30 seconds after the PR is created, it will automatically populate the PR's description field with a generated text that summarizes the changes and provides relevant details.

## Getting Started
To use `auto-pr-writer` in your project, follow these steps:
1. **Add the Action**: Include `auto-pr-writer` in your `.github/workflows` directory.
2. **Create a PR Template**: Set up a PR template in your repository as outlined above.
3. **Open a PR**: Simply open a PR, and `auto-pr-writer` will automatically generate the description.

## Contributions
Contributions to `auto-pr-writer` are welcome! Whether it's feature requests, bug reports, or code contributions, please feel free to open an issue or submit a pull request.
We are looking forward to your feedback!


## License
This project is licensed under [Apache 2.0 License](LICENSE).
