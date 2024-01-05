import json
import os
import re
import sys
from typing import Optional, Tuple, Dict, Any

import requests
from haystack import Pipeline
from haystack.components.connectors import OpenAPIServiceConnector
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage


def generate_pr_text(
    github_repo: str, base_branch: str, pr_branch: str, model_name: str, custom_instruction: Optional[str] = None
) -> str:
    """
    Generates a GitHub Pull Request (PR) text based on user instructions.

    :param github_repo: The GitHub repository in the format 'owner/repo'.
    :type github_repo: str
    :param base_branch: The base branch of the PR.
    :type base_branch: str
    :param pr_branch: The PR branch.
    :type pr_branch: str
    :param model_name: The model to use for PR text generation.
    :type model_name: str
    :param custom_instruction: Optional custom instructions for PR text generation, like "Be brief, one
    sentence per section".
    :type custom_instruction: Optional[str]
    :return: A string containing the generated GitHub PR text in Markdown format, structured into sections like Why,
    What, How to use, etc.
    :rtype: str
    :raises ValueError: If the OPENAI_API_KEY environment variable is not set.
    """
    with open("system_prompt.txt", "r") as file:
        default_system_message = file.read()
    system_message_env = os.environ.get("AUTO_PR_WRITER_SYSTEM_MESSAGE", "")
    # If the user has provided a custom system message, use it instead of the default one
    if system_message_env and system_message_env.strip():
        system_message = system_message_env
    else:
        system_message = default_system_message

    system_message = ChatMessage.from_system(system_message)

    llm_api_key = os.environ.get("OPENAI_API_KEY", None)
    if llm_api_key is None:
        raise ValueError("Please set OPENAI_API_KEY environment variable to your OpenAI API key.")

    # fetch the OpenAPI specification of the GitHub compare service
    openapi_spec = requests.get("https://bit.ly/3tJbUpZ").json()

    # a GitHub access token is required to invoke the GitHub compare service and avoid rate limiting
    service_auth = {"Github API": os.environ.get("GITHUB_TOKEN")}

    invoke_service_pipe = Pipeline()
    invoke_service_pipe.add_component("openapi_container", OpenAPIServiceConnector(service_auth))
    invocation_payload = create_invocation_payload(
        base_ref=base_branch,
        head_ref=pr_branch,
        repository=github_repo.split("/")[0],
        project=github_repo.split("/")[1],
    )

    invocation_payload = json.dumps([invocation_payload])
    service_response = invoke_service_pipe.run(
        data={"messages": [ChatMessage.from_assistant(invocation_payload)], "service_openapi_spec": openapi_spec}
    )

    github_service_response = service_response["openapi_container"]["service_response"]
    if custom_instruction:
        github_pr_prompt_messages = (
            [system_message] + github_service_response + [ChatMessage.from_user(custom_instruction)]
        )
    else:
        github_pr_prompt_messages = [system_message] + github_service_response

    # generate the PR text
    gen_pipe = Pipeline()

    # empirically, max_tokens=2560 should be enough to generate a PR text
    gen_pipe.add_component("llm", OpenAIChatGenerator(model_name=model_name, generation_kwargs={"max_tokens": 2560}))

    final_result = gen_pipe.run(data={"messages": github_pr_prompt_messages})
    return final_result["llm"]["replies"][0].content


def update_pr_description(repo: str, pr_number_id: str, description: str, token: str) -> Tuple[int, Dict[str, Any]]:
    """
    Updates the description of a GitHub Pull Request.

    This function is used to update the PR description on GitHub. It sends a PATCH request to the GitHub API with
    the new description.

    :param repo: The GitHub repository in the format 'owner/repo'.
    :type repo: str
    :param pr_number_id: The number of the pull request to be updated.
    :type pr_number_id: str
    :param description: The new description text for the pull request.
    :type description: str
    :param token: GitHub access token used for authentication.
    :type token: str
    :return: A tuple containing the status code of the response and the response JSON.
    :rtype: tuple
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number_id}"
    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
    data = {"body": description}
    resp = requests.patch(url, headers=headers, data=json.dumps(data))
    return resp.status_code, resp.json()


def extract_custom_instruction(user_instruction: str) -> str:
    """
    Extracts custom instruction from a user instruction string by searching for specific pattern in the user
    instruction string to find and return custom instructions.

    The function uses regular expressions to find the custom instruction following the '@auto-pr-writer-bot' mention
    in the user instruction.

    :param user_instruction: The complete user instruction string, potentially containing custom instructions.
    :type user_instruction: str
    :return: The extracted custom instruction, if found; otherwise, an empty string.
    :rtype: str
    """
    # Search for the message following @auto-pr-writer-bot
    match = re.search(r"@auto-pr-writer-bot\s+(.*)", user_instruction)
    return match.group(1) if match else ""


def create_invocation_payload(base_ref, head_ref, repository, project):
    invocation_payload = {
        "id": "some_irrelevant_id",
        "function": {
            "arguments": f'{{"parameters": {{"basehead": "{base_ref}...{head_ref}", '
            f'"owner": "{repository}", "repo": "{project}"}}}}',
            "name": "compare_branches",
        },
        "type": "function",
    }
    return invocation_payload


def is_verbose():
    return os.environ.get("VERBOSE", "true").lower() == "true"


def contains_skip_instruction(text):
    return bool(re.search(r"\bskip\b", text, re.IGNORECASE))


if __name__ == "__main__":
    if not os.environ.get("GITHUB_TOKEN"):
        print("Please provide GITHUB_TOKEN as environment variable.")
        sys.exit(1)

    user_message = os.environ.get("AUTO_PR_WRITER_USER_MESSAGE")
    custom_user_instruction = extract_custom_instruction(user_message) if user_message else None

    if custom_user_instruction and contains_skip_instruction(custom_user_instruction):
        print("Exiting auto-pr-writer, user instruction contains the word 'skip'.")
        sys.exit(0)

    # Leave "pull_request" as default event type so that we can run the auto-pr-writer locally or via Docker
    # without having to set the event type explicitly
    event_type = os.environ.get("EVENT_NAME", "pull_request")

    # we run the auto-pr-writer for pull requests open and comments on PRs with custom instructions only
    should_run = event_type == "pull_request" or (event_type == "issue_comment" and custom_user_instruction)

    if not should_run:
        print(
            f"Exiting auto-pr-writer, event type is {event_type}."
            "auto-pr-writer runs for pull requests open/reopen and comments on PRs with custom "
            "@auto-pr-writer-bot instructions only"
        )
        sys.exit(0)

    # Fetch required information from environment variables or command-line arguments
    if len(sys.argv) < 2:
        github_repo = os.environ.get("GITHUB_REPOSITORY")
        base_ref = os.environ.get("BASE_REF")
        head_ref = os.environ.get("HEAD_REF")
    else:
        github_repo, base_ref, head_ref = sys.argv[1:4]

    # Validate required parameters
    if not all([github_repo, base_ref, head_ref]):
        print(
            "Please provide GITHUB_REPOSITORY, BASE_REF, HEAD_REF as environment variables or command-line arguments."
        )
        sys.exit(1)

    # Ok, we are go, generate PR text
    generated_pr_text = generate_pr_text(
        github_repo=github_repo,
        base_branch=base_ref,
        pr_branch=head_ref,
        model_name=os.environ.get("GENERATION_MODEL") or "gpt-4-1106-preview",
        custom_instruction=custom_user_instruction,
    )

    if is_verbose():
        print(generated_pr_text)

    # Update the PR description if all conditions are met
    github_token = os.environ.get("GITHUB_TOKEN")
    github_repository = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")

    if all([github_token, github_repository, pr_number, generated_pr_text]):
        status_code, response = update_pr_description(github_repository, pr_number, generated_pr_text, github_token)
        if status_code == 200:
            print(f"Successfully updated PR description for PR #{pr_number} in {github_repository}.")
        else:
            print(f"Failed to update PR description for PR #{pr_number} in {github_repository}.")
            print(f"Status code: {status_code}")
            print(f"Response: {response}")
            sys.exit(status_code)
    else:
        print("Not updating PR description.")
        print("Ensure GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER are set to update the PR description.")
