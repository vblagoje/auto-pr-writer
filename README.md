# Auto PR Writer

## Description
Auto PR Writer is a GitHub Action designed to automatically generate pull request descriptions using Large Language Models (LLMs). It can be customized with system and user-provided prompts to tailor the PR description generation.

## Inputs

### `openai_api_key`
**Required**
The OpenAI API key for authentication.

### `github_token`
**Optional**
GITHUB_TOKEN or a repo scoped Personal Access Token (PAT). Defaults to the GitHub token provided by the GitHub Actions runner.

### `pull_request_number`
**Optional**
The number of the pull request where the action is run. Defaults to the current PR number.

### `github_repository`
**Optional**
The GitHub repository where the pull request is made. Defaults to the current repository.

### `target_branch`
**Optional**
The target branch in the pull request. Defaults to the base branch of the current PR.

### `source_branch`
**Optional**
The source branch in the pull request. Defaults to the head branch of the current PR.

### `system`
**Optional**
System message/prompt to help the model generate the PR description.

### `instruction`
**Optional**
Additional prompt to help the model generate the PR description.

## Usage

Ensure you have set the `OPENAI_API_KEY` and `GITHUB_TOKEN` in your repository's secrets.

## Minimal Example Workflow

Here's a minimal example of how to use the Auto PR Writer in a pull request workflow:

```yaml
name: Pull Request Text Generator Workflow

on:
  pull_request:
    types: [opened]

jobs:
  generate-pr-text:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v2

      - name: Run auto-pr-writer action
        uses: vblagoje/auto-pr-writer@v1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

## Contributing

If you have suggestions for how Auto PR Writer could be improved, or want to report a bug, open an issue or a pull request.

## License
This project is licensed under [Apache 2.0 License](LICENSE).
