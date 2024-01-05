# Auto PR Writer

![License](https://img.shields.io/github/license/vblagoje/auto-pr-writer)
![Last Commit](https://img.shields.io/github/last-commit/vblagoje/auto-pr-writer)
![Docker Pulls](https://img.shields.io/docker/pulls/vblagoje/auto-pr-writer)

## Description
Auto PR Writer is a GitHub Action designed to automatically generate pull request descriptions using Large Language Models (LLMs). By default, it utilizes OpenAI's models, but it also supports integration with a variety of other LLM providers such as fireworks.ai, together.xyz, anyscale, octoai, etc., allowing users to select their preferred provider and LLMs to best suit their needs. This action can be customized with system and user-provided prompts to tailor the PR description generation.

![Auto PR  Demo](https://raw.githubusercontent.com/vblagoje/various/main/auto-pr-writer-optimize.gif)

## Usage

Ensure you have set the `OPENAI_API_KEY` in your repository's secrets. Add a default template for pull requests, clarifying that the pull request description will be automatically generated. Feel free to use our [example](https://github.com/vblagoje/auto-pr-writer/blob/main/.github/pull_request_template.md). Lastly, incorporate a workflow trigger for this GitHub Action. Refer to the Minimal and Advanced example workflows provided below.

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
        uses: actions/checkout@v4

      - name: Run auto-pr-writer action
        uses: vblagoje/auto-pr-writer@v1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

## Advanced Example Workflow

Here's an advanced example of how to use the Auto PR Writer in a pull request workflow:

```yaml
name: Pull Request Text Generator Workflow

on:
  pull_request:
    types: [opened, edited, reopened]
  issue_comment:
    types: [created]

jobs:
  generate-pr-text:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run for PR
        if: github.event_name == 'pull_request'
        uses: vblagoje/auto-pr-writer@v1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          openai_base_url: https://api.fireworks.ai/inference/v1
          generation_model: accounts/fireworks/models/yi-34b-200k-capybara
          user_prompt: ${{ github.event.pull_request.body }}
      - name: Fetch PR details for comment event
        if: github.event_name == 'issue_comment' && github.event.issue.pull_request
        id: pr_details
        uses: octokit/request-action@v2.x
        with:
          route: GET /repos/${{ github.repository }}/pulls/${{ github.event.issue.number }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Run for comment
        if: github.event_name == 'issue_comment' && github.event.issue.pull_request
        uses: vblagoje/auto-pr-writer@v1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          openai_base_url: https://api.fireworks.ai/inference/v1
          user_prompt: ${{ github.event.comment.body }}
          target_branch: ${{ fromJson(steps.pr_details.outputs.data).base.ref }}
          source_branch: ${{ fromJson(steps.pr_details.outputs.data).head.ref }}
          pull_request_number: ${{ github.event.issue.number }}
          generation_model: accounts/fireworks/models/yi-34b-200k-capybara
```
This workflow will run the action on pull request open, edit, and reopen events. It will also run the action on issue comment events on pull requests. Note that it uses fireworks.ai as an LLM provider and a very capable model named accounts/fireworks/models/yi-34b-200k-capybara LLM. This particular LLM has produced PR text descriptions on par with gpt-4.

## GitHub Action Inputs

#### `openai_api_key`
**Required**
The OpenAI API key for authentication. Note that this key could be from other LLM providers as well.

#### `github_token`
**Required**
GITHUB_TOKEN or a repository-scoped Personal Access Token (PAT), defaulting to the GitHub token provided by the GitHub 
Actions runner. It is essential for invoking the GitHub API REST service to retrieve Pull Request details. Using 
GITHUB_TOKEN permits actions to access both public and private repositories, helping to bypass rate limits imposed 
by the GitHub API.

#### `openai_base_url`
**Optional**
The base URL for the OpenAI API. Using this input one can use different LLM providers (e.g. fireworks.ai, together.xyz, anyscale, octoai etc.) Defaults to https://api.openai.com/v1

#### `pull_request_number`
**Optional**
The number of the pull request where the action is run. Defaults to the current PR number.

#### `github_repository`
**Optional**
The GitHub repository where the pull request is made. Defaults to the current repository.

#### `target_branch`
**Optional**
The target branch in the pull request. Defaults to the base branch of the current PR.

#### `source_branch`
**Optional**
The source branch in the pull request. Defaults to the head branch of the current PR.

#### `generation_model`
**Optional**
The generation_model specifies the model to use for PR text generation. While it defaults to gpt-4-1106-preview from OpenAI, users have the flexibility to select from a range of models available from various LLM providers, including but not limited to fireworks.ai, together.xyz, anyscale, octoai, etc. This allows for more tailored and varied text generation capabilities to meet diverse needs and preferences.

#### `system_prompt`
**Optional**
System message/prompt to help the model generate the PR description.

#### `user_prompt`
**Optional**
Additional user prompt to help the model generate the PR description.


## Contributing

If you have suggestions for improving Auto PR Writer or want to report a bug, please feel welcome to open an issue or a pull request. Here are some guidelines to help you contribute effectively:

- **Framework Context**: Auto PR Writer has been developed using the Haystack 2.x framework. Please ensure any development or suggestions are compatible with Haystack features.
- **Focus Areas**: All changes should primarily be focused on the `auto_pr_writer.py` and `action.yml` files. Make sure that modifications align with the overall design and functionality.
- **Open an Issue**: For bugs, feature requests, or other discussions, start by opening an issue. Clearly describe the change you wish to make or the problem you're trying to solve.
- **Submit a Pull Request**: Ready to contribute code or documentation? Submit a pull request. The description will be generated automatically, of course! :-)

## Smoke Test for Docker Image

To confirm the correct operation of the Docker image, perform a smoke test locally using the following steps:

1. **Prepare Your OpenAI API Key**: Ensure your OpenAI API key is ready for use.

2. **Execute the Image**:
   Run the following command in your terminal, replacing `<YOUR_OPENAI_API_KEY>` with your actual API key:

   ```bash
   docker run -e OPENAI_API_KEY=<YOUR_OPENAI_API_KEY> -e GITHUB_TOKEN=<YOUR_GITHUB_TOKEN> vblagoje/auto-pr-writer deepset-ai/haystack main test/benchmarks2.0
   ```

   Modify the parameters `deepset-ai/haystack main test/benchmarks2.0` according to the specific repository main and pr branches, relevant to your use case.

3. **Check the Output**: After execution, verify the output to ensure the image functions as expected.

This test will help you verify the basic functionality of the Docker image. Remember to adjust the command with the appropriate 
project, repository, and branches you wish to compare, and ensure the security of your OpenAI API key throughout this process.

## License
This project is licensed under [Apache 2.0 License](LICENSE).
