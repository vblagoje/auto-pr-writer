import json
import os
import re
import sys
from typing import Optional, Tuple, Dict, Any

import requests

from haystack import Pipeline
from haystack.components.connectors import OpenAPIServiceConnector
from haystack.components.converters import OpenAPIServiceToFunctions
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage


def generate_pr_text(user_instruction: str, custom_instruction: Optional[str] = None) -> str:
    """
    Generates a GitHub Pull Request (PR) text based on user instructions.

    :param user_instruction: A string containing the user's free text command for GitHub PR. For example,
    "Create PR by comparing branches main and rag_services, in project deepset-ai, repo haystack".
    :type user_instruction: str
    :param custom_instruction: Optional custom instructions for PR text generation, like "Be brief, one sentence per section".
    :type custom_instruction: Optional[str]
    :return: A string containing the generated GitHub PR text in markdown format, structured into sections like Why,
    What, How to use, etc.
    :rtype: str
    :raises ValueError: If the OPENAI_API_KEY environment variable is not set.
    """

    default_system_message = """
    As the GitHub PR Expert, your enhanced role now includes the ability to analyze diffs provided by GitHub REST
    service. You'll be given a JSON formatted string consisting of PR commits, description, authors etc. Your primary
    task is crafting GitHub Pull Request text in markdown format, structured into five sections:

    Why:
    What:
    How can it be used:
    How did you test it:
    Notes for the reviewer:

    Always use these sections' names, don't rename them. Make sections text length proportional to the diff size.
    If a diff is really insignificant minimal descriptions are recommended.

    When provided with a diff link or output, you should review and interpret the changes to accurately describe them
    in the PR. Your goal is to offer insightful, accurate descriptions of code changes, enhancing the understanding of
    the PR reviewer.

    Do not use ```markdown and ``` delimiters, just start your response with ### Why markdown format directly.
    """
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

    indexing_pipeline = Pipeline()
    indexing_pipeline.add_component("spec_to_functions", OpenAPIServiceToFunctions())
    results = indexing_pipeline.run(data={"sources": ["https://bit.ly/3tdRUM0"],
                                          "system_messages": [requests.get("https://bit.ly/48eN0ND").text]})

    top_1_document = results["spec_to_functions"]["documents"][0]
    openai_functions_definition = json.loads(top_1_document.content)
    openapi_spec = top_1_document.meta["spec"]

    invoke_service_pipe = Pipeline()
    invoke_service_pipe.add_component("functions_llm", OpenAIChatGenerator(model_name="gpt-3.5-turbo-0613"))
    invoke_service_pipe.add_component("openapi_container", OpenAPIServiceConnector())
    invoke_service_pipe.connect("functions_llm.replies", "openapi_container.messages")

    tools_param = [{"type": "function", "function": openai_functions_definition}]
    tool_choice = {"type": "function", "function": {"name": openai_functions_definition["name"]}}
    service_response = invoke_service_pipe.run(data={"messages": [ChatMessage.from_user(user_instruction)],
                                                     "generation_kwargs": {"tools": tools_param,
                                                                           "tool_choice": tool_choice},
                                                     "service_openapi_spec": openapi_spec})

    github_service_response = service_response["openapi_container"]["service_response"]
    if custom_instruction:
        github_pr_prompt_messages = (
                [system_message] + github_service_response + [ChatMessage.from_user(custom_instruction)]
        )
    else:
        github_pr_prompt_messages = [system_message] + github_service_response

    # generate the PR text
    gen_pipe = Pipeline()
    gen_pipe.add_component("llm", OpenAIChatGenerator(model_name="gpt-4-1106-preview"))

    final_result = gen_pipe.run(data={"messages": github_pr_prompt_messages})
    return final_result["llm"]["replies"][0].content


def update_pr_description(repo, pr_number, description, token) -> Tuple[int, Dict[str, Any]]:
    """
    Updates the description of a GitHub Pull Request.

    This function is used to update the PR description on GitHub. It sends a PATCH request to the GitHub API with
    the new description.

    :param repo: The GitHub repository in the format 'owner/repo'.
    :type repo: str
    :param pr_number: The number of the pull request to be updated.
    :type pr_number: str
    :param description: The new description text for the pull request.
    :type description: str
    :param token: GitHub access token used for authentication.
    :type token: str
    :return: A tuple containing the status code of the response and the response JSON.
    :rtype: tuple
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
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


def main() -> str:
    """
    Main function to generate and optionally update a GitHub PR description.

    This function orchestrates the process of generating a GitHub PR text based on either the command-line
    arguments or environment variables. It also updates the PR description if all required environment
    variables are set.

    :return: The generated GitHub PR text.
    :rtype: str

    :raises SystemExit: If the necessary command-line arguments or environment variables are not provided.
    """

    main_user_instruction = ""
    if len(sys.argv) < 2:
        github_repo = os.environ.get("GITHUB_REPOSITORY")
        base_ref = os.environ.get("BASE_REF")
        head_ref = os.environ.get("HEAD_REF")
        if all([github_repo, base_ref, head_ref]):
            command = (
                f"Compare branches {base_ref} and {head_ref}, in "
                f"project {github_repo.split('/')[0]}, repo {github_repo.split('/')[1]}"
            )
            main_user_instruction = command
    else:
        main_user_instruction = " ".join(sys.argv[1:])

    if not main_user_instruction:
        print(
            "Please provide a free text GitHub PR command, e.g. Compare branches main and your_dev_branch, "
            "in project deepset-ai, repo haystack"
        )
        sys.exit(1)
    user_message = os.environ.get("AUTO_PR_WRITER_USER_MESSAGE", None)
    custom_user_instruction = extract_custom_instruction(user_message) if user_message else None
    return generate_pr_text(main_user_instruction, custom_user_instruction)


if __name__ == "__main__":
    result = main()
    print(result)

    github_token = os.environ.get("GITHUB_TOKEN")
    github_repository = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")

    if all([github_token, github_repository, pr_number, result]):
        status_code, response = update_pr_description(github_repository, pr_number, result, github_token)
        if status_code == 200:
            print(f"Successfully updated PR description for PR #{pr_number} in {github_repository}.")
        else:
            print(f"Failed to update PR description for PR #{pr_number} in {github_repository}.")
            print(f"Status code: {status_code}")
            print(f"Response: {response}")
            sys.exit(status_code)
    else:
        print("Not updating PR description.")
        print("Please set GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER environment variables to update PR description.")
