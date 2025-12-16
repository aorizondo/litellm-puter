import litellm
import os
import asyncio
from scripts.puter_provider import PuterHTTPHandler

os.environ['EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER'] = "True"
os.environ['LITELLM_ANTHROPIC_DISABLE_URL_SUFFIX'] = "True"

print('initialized...')
# response = litellm.completion(
#     # client=PuterHTTPHandler(
#     #     api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoicyIsInYiOiIwLjAuMCIsInUiOiJYWUsyZHUycFFiV2sxL1QybDRxZWVBPT0iLCJ1dSI6ImdxeE5nOU45U2llUkZtUzI2S0VucVE9PSIsImlhdCI6MTc2NDg3NzYxNX0.BuR-Z3hWX-iiKLcI2Zqq8W7z0zlnJK_TXwIs3DepJZc"),
#     # client=PuterHTTPHandler(api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoicyIsInYiOiIwLjAuMCIsInUiOiJMSUVzc25uUlFMNnN4ZDJRMlNyNVh3PT0iLCJ1dSI6InlDTTJicHdpVHRldDhVWllNUEtEUlE9PSIsImlhdCI6MTc2NDkxMTI1NX0.spJRzTXi0VNB5eoyO9XP9_x3dchRvVYQsLJYuxKWy4w"),
#     model="openai/openrouter:deepseek/deepseek-chat",
#     # model="openrouter/openrouter:deepseek/deepseek-chat",
#     # model="anthropic/claude-sonnet-4-5-20250929",
#     api_key="None",
#     api_base="https://api.puter.com/driver/call",
#     messages=[
#         {
#             "role": "user",
#             "content": "Hey, how's it going?",
#         }
#     ],
#
# )
import litellm
import json
# set openai api key
import os
os.environ['OPENAI_API_KEY'] = "" # litellm reads OPENAI_API_KEY from .env and sends the request

# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})


def test_parallel_function_call():
    try:
        # Step 1: send the conversation and available functions to the model
        messages = [{"role": "user", "content": "What's the weather like in San Francisco?"}]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "strict": True,
                    "parameters": {
                        "type": "object",  # ¡CORREGIDO! Debe ser "object"
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                                # Coma eliminada aquí
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"]
                            }
                        },
                        "required": ["location"],
                        "additionalProperties": False  # RECOMENDADO: Evita propiedades extra
                    }
                }
            }
        ]
        response = litellm.completion(
            client=PuterHTTPHandler(
                api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoicyIsInYiOiIwLjAuMCIsInUiOiJYWUsyZHUycFFiV2sxL1QybDRxZWVBPT0iLCJ1dSI6ImdxeE5nOU45U2llUkZtUzI2S0VucVE9PSIsImlhdCI6MTc2NDg3NzYxNX0.BuR-Z3hWX-iiKLcI2Zqq8W7z0zlnJK_TXwIs3DepJZc"),
            # client=PuterHTTPHandler(api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoicyIsInYiOiIwLjAuMCIsInUiOiJMSUVzc25uUlFMNnN4ZDJRMlNyNVh3PT0iLCJ1dSI6InlDTTJicHdpVHRldDhVWllNUEtEUlE9PSIsImlhdCI6MTc2NDkxMTI1NX0.spJRzTXi0VNB5eoyO9XP9_x3dchRvVYQsLJYuxKWy4w"),
            # model="openai/gpt-5.1",
            # model="openrouter/openrouter:deepseek/deepseek-chat",
            model="anthropic/claude-sonnet-4-5-20250929",
            # api_key="None",
            api_key="bg3JDs0lwKVjNfAawuw7IZ5PQ+nuTzSL6sSMfmJXaStCirRItHFTF4k4o6bb9z59ppisFKV9gK6rm635PyiegXCbfHHVPMAF+A5Yf6adBhw/YPF0J8fTL+Nhx0nM2XtE6gnZgEPPPw==",
            api_base="https://api.llm7.io/v1",
            # model="openai/default",
            messages=messages,
            tools=tools,
            # tool_choice="auto",  # auto is default, but we'll be explicit
        )
        print("\nFirst LLM Response:\n", response)
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        print("\nLength of tool calls", len(tool_calls))

        # Step 2: check if the model wanted to call a function
        if tool_calls:
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            available_functions = {
                "get_current_weather": get_current_weather,
            }  # only one function in this example, but you can have multiple
            messages.append(response_message)  # extend conversation with assistant's reply

            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(
                    location=function_args.get("location"),
                    unit=function_args.get("unit"),
                )
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )  # extend conversation with function response
            second_response = litellm.completion(
                api_key="SN74/JKegiYa+CMw5IjICH1LBQ5yGeCrrqCS2P35Y1KYJlDg7KQ3nedhbk2PM2iYjDnbbMco8p9dXPdvdzqk8OIi2LgRUjNwTSzP++rkGo5TRg3tcVrEAuOXWORPOmlJ4wUicZ92eg==",
                api_base="https://api.llm7.io/v1",
                model="gpt-3.5-turbo-1106",
                messages=messages,
            )  # get a new response from the model where it can see the function response
            print("\nSecond LLM response:\n", second_response)
            return second_response
    except Exception as e:
        print(f"Error occurred: {e}")
        raise

test_parallel_function_call()
