# Auto PR Writer

## Description
Auto PR Writer is a GitHub Action designed to generate pull request descriptions automatically using Large Language Models (LLMs). It can be customized with system and user-provided prompts to tailor the PR description generation.

## Inputs

### `system`
**Optional**  
System message/prompt to help the model generate the PR description.

### `instruction`
**Optional**  
Additional prompt to help the model generate the PR description.

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key, used to authenticate requests to OpenAI's APIs.
- `GITHUB_TOKEN`: GitHub token used to authenticate requests to GitHub API for updating PR descriptions.
- `PR_NUMBER`: The pull request number where the action is run.
- `GITHUB_REPOSITORY`: The repository where the pull request is made.
- `BASE_REF`: The base branch in the pull request.
- `HEAD_REF`: The head branch in the pull request.

## Usage

Add the following step to your GitHub Actions workflow:

```yaml
steps:
  - name: Auto PR Writer
    uses: vblagoje/auto-pr-writer@v1    
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Ensure you have set the `OPENAI_API_KEY` in your repository's secrets.

## Example

Here's an example of how to use the Auto PR Writer in a pull request workflow:

```yaml
on: pull_request
  types: [opened]

jobs:
  auto-pr-job:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Auto PR Writer
        uses: vblagoje/auto-pr-writer@v1        
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Contributing

If you have suggestions for improving Auto PR Writer or want to report a bug, open an issue, or make a pull request.
ease feel free to open an issue or submit a pull request.

## License
This project is licensed under [Apache 2.0 License](LICENSE).
